#!/usr/bin/env python3
"""
Script to seed test data for property equipment and consumption.
This creates sample data for demonstration purposes.
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models

def seed_test_property_equipment(db: Session):
    """Add test equipment to the default test property"""
    
    # Find or create test property (assuming it exists from user registration)
    test_property = db.query(models.Property).filter(
        models.Property.user_id == 1
    ).first()
    
    if not test_property:
        print("No test property found. Please create a user and property first.")
        return
    
    # Check if equipment already exists for this property
    existing = db.query(models.PropertyEquipment).filter(
        models.PropertyEquipment.property_id == test_property.id
    ).count()
    
    if existing > 0:
        print(f"Test property already has {existing} equipment items.")
        return
    
    # Get common appliances
    equipments = db.query(models.Equipment).filter(
        models.Equipment.name.in_([
            "Geladeira",
            "Ar Condicionado 12000 BTU",
            "Chuveiro Elétrico",
            "Televisão",
            "Ventilador",
            "Máquina de Lavar",
            "Micro-ondas",
            "Ferro de Passar",
            "Luzes LED"
        ])
    ).all()
    
    # Add sample equipment usage to the property
    sample_usage = [
        {"name": "Geladeira", "quantity": 1, "hours_per_day": 24},
        {"name": "Ar Condicionado 12000 BTU", "quantity": 1, "hours_per_day": 8},
        {"name": "Chuveiro Elétrico", "quantity": 1, "hours_per_day": 1},
        {"name": "Televisão", "quantity": 1, "hours_per_day": 6},
        {"name": "Ventilador", "quantity": 2, "hours_per_day": 4},
        {"name": "Máquina de Lavar", "quantity": 1, "hours_per_day": 1},
        {"name": "Micro-ondas", "quantity": 1, "hours_per_day": 0.5},
        {"name": "Ferro de Passar", "quantity": 1, "hours_per_day": 1},
        {"name": "Luzes LED", "quantity": 15, "hours_per_day": 5},
    ]
    
    for usage in sample_usage:
        equipment = next((e for e in equipments if e.name == usage["name"]), None)
        if equipment:
            prop_equipment = models.PropertyEquipment(
                property_id=test_property.id,
                equipment_id=equipment.id,
                quantity=usage["quantity"],
                hours_per_day=usage["hours_per_day"]
            )
            db.add(prop_equipment)
            print(f"Added: {usage['quantity']}x {usage['name']} ({usage['hours_per_day']} hours/day)")
    
    db.commit()
    print("\nTest data seeded successfully!")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_test_property_equipment(db)
    finally:
        db.close()
