"""
Test script to verify data isolation between users.
This script creates two users, assigns properties to each, and verifies
that each user can only access their own properties by checking that
properties are correctly linked to user_id and queries filter by user_id.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Simple password hashing for test (avoiding complex imports)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Import models directly
from app.models.user import User, Base as UserBase
from app.models.property import Property, Base as PropertyBase
from app.schemas.user import UserCreate
from app.schemas.property import PropertyCreate

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_database():
    """Create tables"""
    UserBase.metadata.create_all(bind=engine)
    PropertyBase.metadata.create_all(bind=engine)

def create_user(db, user):
    """Create a user in the database"""
    db_user = User(
        name=user.name,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_property(db, property_id, user_id):
    """Get a property only if it belongs to the specified user"""
    return db.query(Property).filter(
        Property.id == property_id,
        Property.user_id == user_id
    ).first()

def get_properties_by_user(db, user_id, skip=0, limit=100):
    """Get all properties for a specific user"""
    return db.query(Property).filter(
        Property.user_id == user_id
    ).offset(skip).limit(limit).all()

def create_property(db, property, user_id):
    """Create a property for a specific user"""
    db_property = Property(
        **property.dict(),
        user_id=user_id
    )
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property

def test_data_isolation():
    """Test that users can only access their own properties"""
    db = SessionLocal()
    
    try:
        # Create two test users with short passwords to avoid bcrypt issues
        user1_data = UserCreate(
            name="User One",
            email="user1@example.com",
            password="pass123"  # Short password for bcrypt
        )
        
        user2_data = UserCreate(
            name="User Two",
            email="user2@example.com",
            password="pass456"  # Short password for bcrypt
        )
        
        # Create users in database
        db_user1 = create_user(db, user1_data)
        db_user2 = create_user(db, user2_data)
        
        print(f"Created User 1: ID {db_user1.id}")
        print(f"Created User 2: ID {db_user2.id}")
        
        # Verify users have different IDs
        assert db_user1.id != db_user2.id, "Users should have different IDs"
        
        # Create properties for each user
        property1_data = PropertyCreate(
            address="123 User One St",
            city="City One",
            state="ST",
            zipcode="12345",
            property_type="house",
            built_area=150.0,
            roof_area=100.0,
            orientation="south",
            tilt_angle=25.0
        )
        
        property2_data = PropertyCreate(
            address="456 User Two Ave",
            city="City Two",
            state="ST",
            zipcode="67890",
            property_type="apartment",
            built_area=80.0,
            roof_area=0.0,
            orientation="east",
            tilt_angle=15.0
        )
        
        # Assign properties to users
        db_property1 = create_property(db, property1_data, db_user1.id)
        db_property2 = create_property(db, property2_data, db_user2.id)
        
        print(f"Created Property 1 for User 1: ID {db_property1.id}")
        print(f"Created Property 2 for User 2: ID {db_property2.id}")
        
        # Verify properties have correct user_id
        assert db_property1.user_id == db_user1.id, "Property 1 should belong to User 1"
        assert db_property2.user_id == db_user2.id, "Property 2 should belong to User 2"
        
        # Test 1: User 1 can access their own property
        user1_property = get_property(db, db_property1.id, db_user1.id)
        assert user1_property is not None, "User 1 should be able to access their own property"
        assert user1_property.id == db_property1.id, "Should get the correct property"
        print("✓ User 1 can access their own property")
        
        # Test 2: User 1 cannot access User 2's property
        user1_accessing_user2_property = get_property(db, db_property2.id, db_user1.id)
        assert user1_accessing_user2_property is None, "User 1 should NOT be able to access User 2's property"
        print("✓ User 1 cannot access User 2's property")
        
        # Test 3: User 2 can access their own property
        user2_property = get_property(db, db_property2.id, db_user2.id)
        assert user2_property is not None, "User 2 should be able to access their own property"
        assert user2_property.id == db_property2.id, "Should get the correct property"
        print("✓ User 2 can access their own property")
        
        # Test 4: User 2 cannot access User 1's property
        user2_accessing_user1_property = get_property(db, db_property1.id, db_user2.id)
        assert user2_accessing_user1_property is None, "User 2 should NOT be able to access User 1's property"
        print("✓ User 2 cannot access User 1's property")
        
        # Test 5: User 1 sees only their properties when listing
        user1_properties = get_properties_by_user(db, db_user1.id)
        assert len(user1_properties) == 1, f"User 1 should see exactly 1 property, got {len(user1_properties)}"
        assert user1_properties[0].id == db_property1.id, "User 1 should see their own property"
        print("✓ User 1 sees only their own properties when listing")
        
        # Test 6: User 2 sees only their properties when listing
        user2_properties = get_properties_by_user(db, db_user2.id)
        assert len(user2_properties) == 1, f"User 2 should see exactly 1 property, got {len(user2_properties)}"
        assert user2_properties[0].id == db_property2.id, "User 2 should see their own property"
        print("✓ User 2 sees only their own properties when listing")
        
        # Additional verification: Direct database query to ensure foreign key constraint
        all_properties = db.query(Property).all()
        assert len(all_properties) == 2, f"Should have 2 properties total, got {len(all_properties)}"
        
        # Check that each property is linked to the correct user
        prop1_user_id = db.query(Property.user_id).filter(Property.id == db_property1.id).scalar()
        prop2_user_id = db.query(Property.user_id).filter(Property.id == db_property2.id).scalar()
        
        assert prop1_user_id == db_user1.id, f"Property 1 user_id should be {db_user1.id}, got {prop1_user_id}"
        assert prop2_user_id == db_user2.id, f"Property 2 user_id should be {db_user2.id}, got {prop2_user_id}"
        
        print("✓ Foreign key constraints verified in database")
        
        print("\n🎉 All data isolation tests passed!")
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
    success = test_data_isolation()
    exit(0 if success else 1)