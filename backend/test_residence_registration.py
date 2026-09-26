"""
Test script to verify TASK-04: Residence registration for energy estimation.
This verifies that users can register properties with identification and type,
and that required fields are properly validated.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models and schemas directly
from app.models.property import Property, Base as PropertyBase
from app.models.user import User, Base as UserBase
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyRead
from app.schemas.user import UserCreate

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_database():
    """Create tables"""
    PropertyBase.metadata.create_all(bind=engine)
    UserBase.metadata.create_all(bind=engine)

def test_residence_registration():
    """Test residence registration functionality"""
    db = SessionLocal()
    
    try:
        # Create a test user
        test_user = User(
            name="Test User",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"Created test user: ID {test_user.id}")
        
        # Test 1: Successful property registration with required fields
        print("\n--- Test 1: Successful registration ---")
        property_data = PropertyCreate(
            identification="Minha Casa",
            property_type="house"
        )
        
        db_property = Property(
            **property_data.model_dump(),
            user_id=test_user.id
        )
        db.add(db_property)
        db.commit()
        db.refresh(db_property)
        
        assert db_property.identification == "Minha Casa"
        assert db_property.property_type == "house"
        assert db_property.user_id == test_user.id
        print("✓ Property registered successfully with identification and type")
        
        # Test 2: Property registration with additional fields
        print("\n--- Test 2: Registration with additional fields ---")
        property_data2 = PropertyCreate(
            identification="Apartamento Centro",
            property_type="apartment",
            latitude=-23.5505,
            longitude=-46.6333,
            built_area=80.0,
            roof_area=0.0,
            orientation="north",
            tilt_angle=0.0
        )
        
        db_property2 = Property(
            **property_data2.model_dump(),
            user_id=test_user.id
        )
        db.add(db_property2)
        db.commit()
        db.refresh(db_property2)
        
        assert db_property2.identification == "Apartamento Centro"
        assert db_property2.property_type == "apartment"
        assert db_property2.latitude == -23.5505
        assert db_property2.longitude == -46.6333
        assert db_property2.built_area == 80.0
        assert db_property2.roof_area == 0.0
        assert db_property2.orientation == "north"
        assert db_property2.tilt_angle == 0.0
        print("✓ Property registered successfully with additional fields")
        
        # Test 3: Validation - identification is required
        print("\n--- Test 3: Validation - identification required ---")
        try:
            PropertyCreate(
                identification="",  # Empty string should fail min_length=2
                property_type="house"
            )
            assert False, "Should have failed validation for empty identification"
        except Exception as e:
            assert "identification" in str(e).lower() or "string too short" in str(e).lower()
            print("✓ Empty identification properly rejected")
        
        try:
            PropertyCreate(
                identification=None,  # None should fail
                property_type="house"
            )
            assert False, "Should have failed validation for None identification"
        except Exception as e:
            assert "identification" in str(e).lower() or "none is not allowed" in str(e).lower()
            print("✓ None identification properly rejected")
            
        # Test 4: Validation - property_type is required
        print("\n--- Test 4: Validation - property_type required ---")
        try:
            PropertyCreate(
                identification="Minha Casa",
                property_type=""  # Empty string should fail min_length=2
            )
            assert False, "Should have failed validation for empty property_type"
        except Exception as e:
            assert "property_type" in str(e).lower() or "string too short" in str(e).lower()
            print("✓ Empty property_type properly rejected")
            
        try:
            PropertyCreate(
                identification="Minha Casa",
                property_type=None  # None should fail
            )
            assert False, "Should have failed validation for None property_type"
        except Exception as e:
            assert "property_type" in str(e).lower() or "none is not allowed" in str(e).lower()
            print("✓ None property_type properly rejected")
        
        # Test 5: Reading properties back
        print("\n--- Test 5: Reading properties ---")
        properties = db.query(Property).filter(Property.user_id == test_user.id).all()
        assert len(properties) == 2, f"Expected 2 properties, got {len(properties)}"
        
        # Find our test properties
        casa_prop = next((p for p in properties if p.identification == "Minha Casa"), None)
        apt_prop = next((p for p in properties if p.identification == "Apartamento Centro"), None)
        
        assert casa_prop is not None, "Should find 'Minha Casa' property"
        assert apt_prop is not None, "Should find 'Apartamento Centro' property"
        assert casa_prop.property_type == "house"
        assert apt_prop.property_type == "apartment"
        print("✓ Properties correctly stored and retrieved")
        
        # Test 6: Schema conversion
        print("\n--- Test 6: Schema conversion ---")
        property_read = PropertyRead.model_validate(casa_prop)
        assert property_read.identification == "Minha Casa"
        assert property_read.property_type == "house"
        assert property_read.id == casa_prop.id
        assert property_read.user_id == test_user.id
        print("✓ PropertyRead schema conversion works correctly")
        
        # Test 7: PropertyUpdate schema
        print("\n--- Test 7: PropertyUpdate schema ---")
        update_data = PropertyUpdate(
            identification="Minha Casa Atualizada",
            property_type="house"
        )
        assert update_data.identification == "Minha Casa Atualizada"
        assert update_data.property_type == "house"
        print("✓ PropertyUpdate schema works correctly")
        
        print("\n🎉 All residence registration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    setup_database()
    success = test_residence_registration()
    exit(0 if success else 1)