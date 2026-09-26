"""
Final verification test for TASK-04: Residence registration for energy estimation.
This verifies that users can register properties with identification and type,
and that required fields are properly validated.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

def test_residence_registration():
    """Test residence registration functionality"""
    # Setup fresh database for this test
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Import and setup database FIRST
    from app.database import Base, get_db
    
    # Import models BEFORE creating tables so they're registered with Base
    from app.models.user import User
    from app.models.property import Property
    from app.auth import create_access_token
    from app.schemas.user import UserCreate
    
    # NOW create tables (after models are imported)
    Base.metadata.drop_all(bind=engine)  # Clean slate
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # Import app AFTER database setup to avoid conflicts
    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client AFTER database setup
    client = TestClient(app)
    
    try:
        # Create a test user directly in DB for testing
        db = TestingSessionLocal()
        test_user = User(
            name="Test User",
            email="test@example.com",
            hashed_password="hashed_password",  # Simplified for test
            is_active=True,
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        db.close()
        
        # Create access token for authentication
        access_token = create_access_token(data={"sub": test_user.email})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        print(f"Created test user: ID {test_user.id}")
        
        # Test 1: Successful property registration with required fields
        print("\n--- Test 1: Successful registration ---")
        response = client.post(
            "/properties/",
            json={
                "identification": "Minha Casa",
                "property_type": "house"
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["identification"] == "Minha Casa"
        assert data["property_type"] == "house"
        assert "id" in data
        assert data["user_id"] == test_user.id
        print("✓ Property registered successfully with identification and type")
        
        # Test 2: Property registration with additional fields
        print("\n--- Test 2: Registration with additional fields ---")
        response = client.post(
            "/properties/",
            json={
                "identification": "Apartamento Centro",
                "property_type": "apartment",
                "latitude": -23.5505,
                "longitude": -46.6333,
                "built_area": 80.0,
                "roof_area": 0.0,
                "orientation": "north",
                "tilt_angle": 0.0
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["identification"] == "Apartamento Centro"
        assert data["property_type"] == "apartment"
        assert data["latitude"] == -23.5505
        assert data["longitude"] == -46.6333
        assert data["built_area"] == 80.0
        assert data["roof_area"] == 0.0
        assert data["orientation"] == "north"
        assert data["tilt_angle"] == 0.0
        print("✓ Property registered successfully with additional fields")
        
        # Test 3: Validation - identification is required (too short)
        print("\n--- Test 3: Validation - identification too short ---")
        response = client.post(
            "/properties/",
            json={
                "identification": "A",  # Too short (min_length=2)
                "property_type": "house"
            },
            headers=headers
        )
        
        assert response.status_code == 422, f"Expected 422 for validation error, got {response.status_code}"
        error_data = response.json()
        assert any("identification" in str(error).lower() for error in error_data.get("detail", []))
        print("✓ Short identification properly rejected with 422")
        
        # Test 4: Validation - identification is required (missing)
        print("\n--- Test 4: Validation - identification missing ---")
        response = client.post(
            "/properties/",
            json={
                "property_type": "house"
                # identification missing
            },
            headers=headers
        )
        
        assert response.status_code == 422, f"Expected 422 for validation error, got {response.status_code}"
        error_data = response.json()
        assert any("identification" in str(error).lower() for error in error_data.get("detail", []))
        print("✓ Missing identification properly rejected with 422")
        
        # Test 5: Validation - property_type is required (too short)
        print("\n--- Test 5: Validation - property_type too short ---")
        response = client.post(
            "/properties/",
            json={
                "identification": "Minha Casa",
                "property_type": "h"  # Too short (min_length=2)
            },
            headers=headers
        )
        
        assert response.status_code == 422, f"Expected 422 for validation error, got {response.status_code}"
        error_data = response.json()
        assert any("property_type" in str(error).lower() for error in error_data.get("detail", []))
        print("✓ Short property_type properly rejected with 422")
        
        # Test 6: Validation - property_type is required (missing)
        print("\n--- Test 6: Validation - property_type missing ---")
        response = client.post(
            "/properties/",
            json={
                "identification": "Minha Casa"
                # property_type missing
            },
            headers=headers
        )
        
        assert response.status_code == 422, f"Expected 422 for validation error, got {response.status_code}"
        error_data = response.json()
        assert any("property_type" in str(error).lower() for error in error_data.get("detail", []))
        print("✓ Missing property_type properly rejected with 422")
        
        # Test 7: Reading properties back via API
        print("\n--- Test 7: Reading properties ---")
        response = client.get("/properties/", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        print(f"Received {len(data)} properties: {[p['identification'] for p in data]}")
        assert isinstance(data, list), "Expected list of properties"
        assert len(data) == 2, f"Expected 2 properties, got {len(data)}"
        
        # Find our test properties
        casa_prop = next((p for p in data if p["identification"] == "Minha Casa"), None)
        apt_prop = next((p for p in data if p["identification"] == "Apartamento Centro"), None)
        
        assert casa_prop is not None, "Should find 'Minha Casa' property"
        assert apt_prop is not None, "Should find 'Apartamento Centro' property"
        assert casa_prop["property_type"] == "house"
        assert apt_prop["property_type"] == "apartment"
        print("✓ Properties correctly stored and retrieved")
        
        # Test 8: Reading specific property via API
        print("\n--- Test 8: Reading specific property ---")
        response = client.get(f"/properties/{casa_prop['id']}", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["identification"] == "Minha Casa"
        assert data["property_type"] == "house"
        assert data["id"] == casa_prop["id"]
        print("✓ Specific property correctly retrieved")
        
        # Test 9: Updating property via API
        print("\n--- Test 9: Updating property ---")
        response = client.put(
            f"/properties/{casa_prop['id']}",
            json={
                "identification": "Minha Casa Atualizada",
                "property_type": "house"
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["identification"] == "Minha Casa Atualizada"
        assert data["property_type"] == "house"
        assert data["id"] == casa_prop["id"]
        print("✓ Property correctly updated")
        
        # Test 10: Authentication required - no token
        print("\n--- Test 10: Authentication required ---")
        response = client.post(
            "/properties/",
            json={
                "identification": "Should Fail",
                "property_type": "house"
            }
            # No headers - should fail
        )
        
        assert response.status_code == 401, f"Expected 401 for missing auth, got {response.status_code}"
        print("✓ Authentication properly required for property endpoints")
        
        # Test 11: Authentication required - invalid token
        print("\n--- Test 11: Invalid token rejected ---")
        response = client.post(
            "/properties/",
            json={
                "identification": "Should Fail",
                "property_type": "house"
            },
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == 401, f"Expected 401 for invalid token, got {response.status_code}"
        print("✓ Invalid token properly rejected")
        
        print("\n🎉 All TASK-04 tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        print("Cleaning up database...")
        Base.metadata.drop_all(bind=engine)
        # Clean dependency overrides
        app.dependency_overrides.clear()

if __name__ == "__main__":
    print("Starting TASK-04 verification test...")
    success = test_residence_registration()
    print(f"Test result: {'PASS' if success else 'FAIL'}")
    exit(0 if success else 1)