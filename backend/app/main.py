from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Generator

from .database import Base, engine, SessionLocal
from . import crud.user
from .schemas import user as user_schema

# Create database tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()


@app.post("/users/", response_model=user_schema.UserRead)
async def register_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    db_user = crud.user.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        hashed_pw = user.hashed_password  # store as plain for now
        db_user = crud.user.create_user(db=db, user=user)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    return db_user