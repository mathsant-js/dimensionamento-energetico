import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import auth, main
from app.database import Base


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class ApiFlowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        main.app.dependency_overrides[main.get_db] = override_get_db
        main.app.dependency_overrides[auth.get_db] = override_get_db
        cls.client = TestClient(main.app)

    @classmethod
    def tearDownClass(cls):
        main.app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)

    def register_and_login(self, suffix):
        email = f"user-{suffix}@example.com"
        response = self.client.post("/users/", json={
            "name": f"User {suffix}", "email": email, "password": "password123",
        })
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/token", json={"email": email, "password": "password123"})
        self.assertEqual(response.status_code, 200)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_authenticated_property_lifecycle_and_isolation(self):
        owner_headers = self.register_and_login("owner")
        other_headers = self.register_and_login("other")
        property_data = {
            "identification": "Casa Solar", "property_type": "house",
            "address": "Rua do Sol, 10", "city": "Sao Paulo", "state": "SP", "zipcode": "01000-000",
        }

        response = self.client.post("/properties/", json=property_data, headers=owner_headers)
        self.assertEqual(response.status_code, 200)
        property_id = response.json()["id"]
        self.assertEqual(response.json()["address"], property_data["address"])

        self.assertEqual(self.client.get("/properties/", headers=other_headers).json(), [])
        self.assertEqual(self.client.get(f"/properties/{property_id}", headers=other_headers).status_code, 404)
        self.assertEqual(
            self.client.put(f"/properties/{property_id}", json={"city": "Campinas"}, headers=other_headers).status_code,
            404,
        )
        self.assertEqual(self.client.delete(f"/properties/{property_id}", headers=other_headers).status_code, 404)

        response = self.client.put(
            f"/properties/{property_id}", json={"identification": "Casa Atualizada", "built_area": 120}, headers=owner_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["identification"], "Casa Atualizada")
        self.assertEqual(response.json()["built_area"], 120)

        self.assertEqual(self.client.delete(f"/properties/{property_id}", headers=owner_headers).status_code, 200)
        self.assertEqual(self.client.get("/properties/", headers=owner_headers).json(), [])

    def test_equipment_catalog_and_property_equipment_lifecycle(self):
        self.assertEqual(self.client.get("/equipments/").status_code, 401)

        owner_headers = self.register_and_login("equipment-owner")
        other_headers = self.register_and_login("equipment-other")
        property_response = self.client.post("/properties/", json={
            "identification": "Casa com equipamentos", "property_type": "house",
        }, headers=owner_headers)
        self.assertEqual(property_response.status_code, 200)
        property_id = property_response.json()["id"]

        equipment_response = self.client.post("/equipments/", json={
            "name": "Equipamento de teste", "category": "Teste", "power_watts": 1000,
        }, headers=owner_headers)
        self.assertEqual(equipment_response.status_code, 200)
        equipment_id = equipment_response.json()["id"]

        catalog_response = self.client.get("/equipments/", headers=owner_headers)
        self.assertEqual(catalog_response.status_code, 200)
        self.assertTrue(any(item["id"] == equipment_id for item in catalog_response.json()))

        link_response = self.client.post(
            f"/properties/{property_id}/equipments/",
            json={"equipment_id": equipment_id, "quantity": 2, "hours_per_day": 3},
            headers=owner_headers,
        )
        self.assertEqual(link_response.status_code, 200)
        property_equipment_id = link_response.json()["id"]

        duplicate_response = self.client.post(
            f"/properties/{property_id}/equipments/",
            json={"equipment_id": equipment_id, "quantity": 1, "hours_per_day": 1},
            headers=owner_headers,
        )
        self.assertEqual(duplicate_response.status_code, 409)
        self.assertEqual(duplicate_response.json()["detail"], "Equipment is already linked to this property")

        invalid_usage_response = self.client.post(
            f"/properties/{property_id}/equipments/",
            json={"equipment_id": equipment_id, "quantity": 0, "hours_per_day": 25},
            headers=owner_headers,
        )
        self.assertEqual(invalid_usage_response.status_code, 422)

        self.assertEqual(
            self.client.get(f"/properties/{property_id}/equipments/", headers=other_headers).status_code,
            404,
        )
        self.assertEqual(
            self.client.put(
                f"/properties/{property_id}/equipments/{property_equipment_id}",
                json={"quantity": 4},
                headers=other_headers,
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.delete(
                f"/properties/{property_id}/equipments/{property_equipment_id}",
                headers=other_headers,
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(f"/properties/{property_id}/consumption-report", headers=other_headers).status_code,
            404,
        )

        update_response = self.client.put(
            f"/properties/{property_id}/equipments/{property_equipment_id}",
            json={"quantity": 3, "hours_per_day": 2},
            headers=owner_headers,
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["quantity"], 3)
        self.assertEqual(update_response.json()["hours_per_day"], 2)

        report_response = self.client.get(
            f"/properties/{property_id}/consumption-report", headers=owner_headers
        )
        self.assertEqual(report_response.status_code, 200)
        report = report_response.json()
        self.assertEqual(report["items"][0]["monthly_consumption_kwh"], 180)
        self.assertEqual(report["total_monthly_consumption_kwh"], 180)

        self.assertEqual(
            self.client.delete(
                f"/properties/{property_id}/equipments/{property_equipment_id}",
                headers=owner_headers,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(f"/properties/{property_id}/equipments/", headers=owner_headers).json(), []
        )
