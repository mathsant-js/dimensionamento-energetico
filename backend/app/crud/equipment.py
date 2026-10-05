from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, schemas
from datetime import datetime

# Equipment CRUD

def get_equipment(db: Session, equipment_id: int):
    return db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()

def get_all_equipments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Equipment).offset(skip).limit(limit).all()

def create_equipment(db: Session, equipment: schemas.EquipmentCreate):
    db_equipment = models.Equipment(
        **equipment.model_dump()
    )
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

# PropertyEquipment CRUD

def get_property_equipment(db: Session, property_equipment_id: int):
    return db.query(models.PropertyEquipment).filter(
        models.PropertyEquipment.id == property_equipment_id
    ).first()


def get_property_equipment_by_equipment_id(db: Session, property_id: int, equipment_id: int):
    return db.query(models.PropertyEquipment).filter(
        models.PropertyEquipment.property_id == property_id,
        models.PropertyEquipment.equipment_id == equipment_id,
    ).first()

def get_property_equipments(db: Session, property_id: int, user_id: int, skip: int = 0, limit: int = 100):
    query = db.query(models.PropertyEquipment).join(
        models.Property,
        models.Property.id == models.PropertyEquipment.property_id
    ).filter(
        models.PropertyEquipment.property_id == property_id
    )

    if user_id is not None:
        query = query.filter(models.Property.user_id == user_id)

    return query.offset(skip).limit(limit).all()

def create_property_equipment(
    db: Session, 
    property_id: int, 
    property_equipment: schemas.PropertyEquipmentCreate,
    user_id: int
):
    if user_id is not None:
        property_obj = db.query(models.Property).filter(
            models.Property.id == property_id,
            models.Property.user_id == user_id
        ).first()
        if property_obj is None:
            return None

    db_property_equipment = models.PropertyEquipment(
        property_id=property_id,
        **property_equipment.model_dump()
    )
    db.add(db_property_equipment)
    db.commit()
    db.refresh(db_property_equipment)
    return db_property_equipment

def update_property_equipment(
    db: Session,
    property_equipment_id: int,
    property_equipment: schemas.PropertyEquipmentUpdate,
    user_id: int
):
    db_property_equipment = get_property_equipment(db, property_equipment_id)
    if db_property_equipment and user_id is not None:
        property_obj = db.query(models.Property).filter(
            models.Property.id == db_property_equipment.property_id,
            models.Property.user_id == user_id
        ).first()
        if property_obj is None:
            return None

    if db_property_equipment:
        update_data = property_equipment.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_property_equipment, key, value)
        db.commit()
        db.refresh(db_property_equipment)
    return db_property_equipment

def delete_property_equipment(db: Session, property_equipment_id: int, user_id: int):
    db_property_equipment = get_property_equipment(db, property_equipment_id)
    if db_property_equipment and user_id is not None:
        property_obj = db.query(models.Property).filter(
            models.Property.id == db_property_equipment.property_id,
            models.Property.user_id == user_id
        ).first()
        if property_obj is None:
            return None

    if db_property_equipment:
        db.delete(db_property_equipment)
        db.commit()
    return db_property_equipment

# Consumption Report

def get_consumption_report(db: Session, property_id: int, user_id: int):
    """Get consumption report for a property"""
    # Verify that the property belongs to the user
    property_obj = db.query(models.Property).filter(
        models.Property.id == property_id,
        models.Property.user_id == user_id
    ).first()
    
    if not property_obj:
        return None
    
    # Get all property equipments with their equipment details
    property_equipments = db.query(models.PropertyEquipment).filter(
        models.PropertyEquipment.property_id == property_id
    ).all()
    
    # Calculate consumption for each equipment
    items = []
    total_consumption = 0.0
    
    for pe in property_equipments:
        # Formula: (power_watts * quantity * hours_per_day * 30) / 1000
        monthly_consumption_kwh = (pe.equipment.power_watts * pe.quantity * pe.hours_per_day * 30) / 1000
        
        item = schemas.ConsumptionReportItem(
            id=pe.id,
            equipment_name=pe.equipment.name,
            power_watts=pe.equipment.power_watts,
            quantity=pe.quantity,
            hours_per_day=pe.hours_per_day,
            monthly_consumption_kwh=monthly_consumption_kwh
        )
        items.append(item)
        total_consumption += monthly_consumption_kwh
    
    report = schemas.ConsumptionReport(
        property_id=property_id,
        property_name=property_obj.identification,
        property_type=property_obj.property_type,
        items=items,
        total_monthly_consumption_kwh=total_consumption,
        created_at=datetime.now()
    )
    
    return report
