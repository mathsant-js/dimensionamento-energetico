from sqlalchemy.orm import Session
from . import models
from .schemas import user as user_schema

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: user_schema.UserCreate):
    # Check if email already exists
    db_user = get_user_by_email(db, user.email)
    if db_user:
        return None  # Duplicate email
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=user.hashed_password,
        is_active=user.is_active,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user