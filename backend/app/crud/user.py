from sqlalchemy.orm import Session
from . import models
from .schemas import user as user_schema
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_user(db: Session, user: user_schema.UserCreate):
    # Check if email already exists
    db_user = get_user_by_email(db, user.email)
    if db_user:
        return None  # Duplicate email
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user