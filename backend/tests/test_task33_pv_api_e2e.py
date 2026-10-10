"""TASK-33: fluxo HTTP completo e isolamento das propostas fotovoltaicas."""

from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

import httpx
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db as database_get_db
from app.main import app, get_db as main_get_db


class PVApiEndToEndTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="task33-")
        database_path = Path(self.temp_dir.name) / "e2e.sqlite3"
        self.engine = create_engine(
            f"sqlite:///{database_path}",
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False
        )

        async def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        # main.py ainda possui uma dependência local para as rotas da Sprint 1,
        # enquanto autenticação e o router FV usam app.database.get_db.
        app.dependency_overrides[main_get_db] = override_db
        app.dependency_overrides[database_get_db] = override_db
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        self.temp_dir.cleanup()

    async def register_and_login(self, name, email):
        password = "senha-segura-123"
        registered = await self.client.post(
            "/users/", json={"name": name, "email": email, "password": password}
        )
        self.assertEqual(200, registered.status_code, registered.text)
        logged_in = await self.client.post(
            "/token", json={"email": email, "password": password}
        )
        self.assertEqual(200, logged_in.status_code, logged_in.text)
        return {"Authorization": f"Bearer {logged_in.json()['access_token']}"}

    async def create_property(self, headers, identification):
        response = await self.client.post(
            "/properties/",
            headers=headers,
            json={
                "identification": identification,
                "property_type": "house",
                "city": "São Paulo",
                "state": "SP",
            },
        )
        self.assertEqual(200, response.status_code, response.text)
        return response.json()

    async def selected_payload(self, headers, property_id, **changes):
        payload = {
            "hsp_kwh_m2_day": "5",
            "hsp_source": "Entrada manual reproduzível da TASK-33",
            "hsp_source_date": "2026-10-10",
            "target_offset_fraction": "1",
            "performance_ratio": "0.8",
            **changes,
        }
        simulation = await self.client.post(
            f"/api/properties/{property_id}/pv/simulations",
            headers=headers,
            json=payload,
        )
        self.assertEqual(200, simulation.status_code, simulation.text)
        result = simulation.json()
        payload["module_catalog_id"] = result["selected_module"]["catalog_id"]
        payload["inverter_catalog_id"] = result["compatible_inverters"][0][
            "catalog_id"
        ]
        return payload, result

    async def test_two_users_complete_pv_flow_and_cross_user_isolation(self):
        owner_headers = await self.register_and_login(
            "Usuária proprietária", "owner-task33@example.com"
        )
        intruder_headers = await self.register_and_login(
            "Usuário externo", "intruder-task33@example.com"
        )
        owner_property = await self.create_property(owner_headers, "Casa da proprietária")
        intruder_property = await self.create_property(
            intruder_headers, "Casa do usuário externo"
        )

        equipment = await self.client.post(
            "/equipments/",
            headers=owner_headers,
            json={"name": "Carga de teste 1 kW", "category": "Teste", "power_watts": 1000},
        )
        self.assertEqual(200, equipment.status_code, equipment.text)
        linked = await self.client.post(
            f"/properties/{owner_property['id']}/equipments/",
            headers=owner_headers,
            json={
                "equipment_id": equipment.json()["id"],
                "quantity": 1,
                "hours_per_day": 10,
            },
        )
        self.assertEqual(200, linked.status_code, linked.text)

        consumption = await self.client.get(
            f"/properties/{owner_property['id']}/consumption-report",
            headers=owner_headers,
        )
        self.assertEqual(200, consumption.status_code, consumption.text)
        self.assertEqual(300.0, consumption.json()["total_monthly_consumption_kwh"])

        without_battery, simulation = await self.selected_payload(
            owner_headers, owner_property["id"]
        )
        self.assertEqual(
            Decimal("300"),
            Decimal(simulation["calculation"]["reference_consumption"]["value"]),
        )
        self.assertEqual(
            Decimal("300"), Decimal(simulation["calculation"]["target_energy"]["value"])
        )
        self.assertEqual(
            Decimal("2.5"),
            Decimal(simulation["calculation"]["required_pv_power"]["value"]),
        )
        created_without = await self.client.post(
            f"/api/properties/{owner_property['id']}/pv/proposals",
            headers=owner_headers,
            json=without_battery,
        )
        self.assertEqual(201, created_without.status_code, created_without.text)
        no_battery = created_without.json()
        self.assertFalse(no_battery["battery_requested"])
        self.assertEqual("0.00", no_battery["batteries_cost_brl"])
        self.assertEqual(
            {"module", "inverter"},
            {item["item_type"] for item in no_battery["items"]},
        )

        batteries = await self.client.get(
            "/api/pv/datasets/batteries", headers=owner_headers
        )
        self.assertEqual(200, batteries.status_code, batteries.text)
        with_battery, battery_simulation = await self.selected_payload(
            owner_headers,
            owner_property["id"],
            autonomy_hours="12",
            battery_catalog_id=batteries.json()[0]["id"],
            additional_costs=[{"description": "Instalação", "value_brl": "1500.00"}],
        )
        self.assertTrue(battery_simulation["storage"]["storage_requested"])
        created_with = await self.client.post(
            f"/api/properties/{owner_property['id']}/pv/proposals",
            headers=owner_headers,
            json=with_battery,
        )
        self.assertEqual(201, created_with.status_code, created_with.text)
        battery_proposal = created_with.json()
        self.assertTrue(battery_proposal["battery_requested"])
        self.assertGreater(Decimal(battery_proposal["batteries_cost_brl"]), 0)
        self.assertEqual(
            {"module", "inverter", "battery", "additional"},
            {item["item_type"] for item in battery_proposal["items"]},
        )
        expected_total = sum(
            Decimal(battery_proposal[field])
            for field in (
                "modules_cost_brl",
                "inverter_cost_brl",
                "batteries_cost_brl",
                "additional_cost_brl",
            )
        )
        self.assertEqual(expected_total, Decimal(battery_proposal["total_cost_brl"]))

        proposal_id = battery_proposal["id"]
        proposal_url = (
            f"/api/properties/{owner_property['id']}/pv/proposals/{proposal_id}"
        )
        for method, kwargs in (
            (self.client.get, {}),
            (self.client.put, {"json": with_battery}),
            (self.client.delete, {}),
        ):
            denied = await method(proposal_url, headers=intruder_headers, **kwargs)
            self.assertEqual(404, denied.status_code, denied.text)

        foreign_property_attempt = await self.client.get(
            f"/api/properties/{intruder_property['id']}/pv/proposals/{proposal_id}",
            headers=owner_headers,
        )
        self.assertEqual(404, foreign_property_attempt.status_code)

        persisted = await self.client.get(proposal_url, headers=owner_headers)
        self.assertEqual(200, persisted.status_code, persisted.text)
        self.assertEqual(battery_proposal, persisted.json())
        listed = await self.client.get(
            f"/api/properties/{owner_property['id']}/pv/proposals",
            headers=owner_headers,
        )
        self.assertEqual(
            [battery_proposal["id"], no_battery["id"]],
            [proposal["id"] for proposal in listed.json()],
        )


if __name__ == "__main__":
    unittest.main()
