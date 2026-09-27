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
