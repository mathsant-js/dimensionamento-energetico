from sqlalchemy.orm import Session
from . import models, schemas

def get_property(db: Session, property_id: int, user_id: int):
    return db.query(models.Property).filter(
        models.Property.id == property_id,
        models.Property.user_id == user_id
    ).first()

def get_properties_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Property).filter(
        models.Property.user_id == user_id
    ).offset(skip).limit(limit).all()

def create_property(db: Session, property: schemas.PropertyCreate, user_id: int):
    db_property = models.Property(
        **property.dict(),
        user_id=user_id
    )
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property

def update_property(db: Session, property_id: int, property: schemas.PropertyUpdate, user_id: int):
    db_property = get_property(db, property_id, user_id)
    if db_property:
        update_data = property.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_property, key, value)
        db.commit()
        db.refresh(db_property)
    return db_property

def delete_property(db: Session, property_id: int, user_id: int):
    db_property = get_property(db, property_id, user_id)
    if db_property:
        db.delete(db_property)
        db.commit()
    return db_property