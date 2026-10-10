import unittest

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_current_active_user
from app.database import Base, get_db
from app.main import app
from app.models import Equipment, Property, PropertyEquipment, User


class PVApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.user = User(name="U1", email="u1@api.test", hashed_password="x", is_active=True)
        self.other = User(name="U2", email="u2@api.test", hashed_password="x", is_active=True)
        self.db.add_all([self.user, self.other])
        self.db.flush()
        self.property = Property(
            user_id=self.user.id, identification="Casa", property_type="house"
        )
        self.empty_property = Property(
            user_id=self.user.id, identification="Casa vazia", property_type="house"
        )
        self.other_property = Property(
            user_id=self.other.id, identification="Outra", property_type="house"
        )
        equipment = Equipment(name="Carga", category="Teste", power_watts=1000)
        self.db.add_all([self.property, self.empty_property, self.other_property, equipment])
        self.db.flush()
        self.db.add(PropertyEquipment(
            property_id=self.property.id,
            equipment_id=equipment.id,
            quantity=1,
            hours_per_day=10,
        ))
        self.db.commit()

        async def override_db():
            yield self.db

        app.dependency_overrides[get_db] = override_db
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://test")
        self.payload = {
            "hsp_kwh_m2_day": "5",
            "hsp_source": "Entrada manual de teste",
            "hsp_source_date": "2026-10-09",
            "target_offset_fraction": "1",
            "performance_ratio": "0.8",
        }

    async def asyncTearDown(self):
        await self.client.aclose()
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def authenticate_as(self, user):
        async def authenticated_user():
            return user
        app.dependency_overrides[get_current_active_user] = authenticated_user

    async def test_catalog_requires_authentication_and_openapi_documents_contract(self):
        response = await self.client.get("/api/pv/datasets/modules")
        self.assertEqual(401, response.status_code)

        schema = (await self.client.get("/openapi.json")).json()
        operation = schema["paths"]["/api/properties/{property_id}/pv/simulations"]["post"]
        self.assertTrue({"401", "404", "409", "422"}.issubset(operation["responses"]))

    async def test_simulation_derives_consumption_and_returns_selection_diagnostics(self):
        self.authenticate_as(self.user)
        response = await self.client.post(
            f"/api/properties/{self.property.id}/pv/simulations", json=self.payload
        )
        self.assertEqual(200, response.status_code, response.text)
        data = response.json()
        self.assertEqual("300.0", data["calculation"]["reference_consumption"]["value"])
        self.assertGreater(len(data["module_alternatives"]), 0)
        self.assertGreater(len(data["compatible_inverters"]), 0)
        self.assertIn("rejected_inverters", data)
        self.assertIsNone(data["budget"])

    async def test_create_list_get_update_delete_revalidates_server_side(self):
        self.authenticate_as(self.user)
        simulation = (await self.client.post(
            f"/api/properties/{self.property.id}/pv/simulations", json=self.payload
        )).json()
        selected = dict(self.payload)
        selected["module_catalog_id"] = simulation["selected_module"]["catalog_id"]
        selected["inverter_catalog_id"] = simulation["compatible_inverters"][0]["catalog_id"]

        created = await self.client.post(
            f"/api/properties/{self.property.id}/pv/proposals", json=selected
        )
        self.assertEqual(201, created.status_code, created.text)
        proposal = created.json()
        self.assertGreater(float(proposal["total_cost_brl"]), 0)
        self.assertEqual(2, len(proposal["items"]))

        proposal_id = proposal["id"]
        listed = await self.client.get(
            f"/api/properties/{self.property.id}/pv/proposals"
        )
        self.assertEqual([proposal_id], [item["id"] for item in listed.json()])
        fetched = await self.client.get(
            f"/api/properties/{self.property.id}/pv/proposals/{proposal_id}"
        )
        self.assertEqual(proposal_id, fetched.json()["id"])

        selected["target_offset_fraction"] = "0.8"
        updated = await self.client.put(
            f"/api/properties/{self.property.id}/pv/proposals/{proposal_id}", json=selected
        )
        self.assertEqual(200, updated.status_code, updated.text)
        self.assertEqual("0.80000", updated.json()["target_offset_fraction"])

        deleted = await self.client.delete(
            f"/api/properties/{self.property.id}/pv/proposals/{proposal_id}"
        )
        self.assertEqual(204, deleted.status_code)
        missing = await self.client.get(
            f"/api/properties/{self.property.id}/pv/proposals/{proposal_id}"
        )
        self.assertEqual(404, missing.status_code)

    async def test_404_does_not_reveal_foreign_resources_and_422_and_409_are_stable(self):
        self.authenticate_as(self.user)
        foreign = await self.client.post(
            f"/api/properties/{self.other_property.id}/pv/simulations", json=self.payload
        )
        self.assertEqual(404, foreign.status_code)

        invalid = await self.client.post(
            f"/api/properties/{self.property.id}/pv/simulations",
            json={**self.payload, "hsp_kwh_m2_day": "0"},
        )
        self.assertEqual(422, invalid.status_code)

        no_consumption = await self.client.post(
            f"/api/properties/{self.empty_property.id}/pv/simulations", json=self.payload
        )
        self.assertEqual(409, no_consumption.status_code)
        self.assertEqual(
            "reference_consumption_kwh_month", no_consumption.json()["detail"]["field"]
        )


if __name__ == "__main__":
    unittest.main()
