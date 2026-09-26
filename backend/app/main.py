from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Generator
from datetime import timedelta
from typing import List

from .database import Base, engine, SessionLocal
from . import crud.user, crud.property
from .schemas import user as user_schema, property as property_schema
from .auth import authenticate_user, create_access_token, get_current_active_user
from .schemas.user import Token
from .config import settings

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
    # Create user (password will be hashed inside CRUD)
    db_user = crud.user.create_user(db=db, user=user)
    return db_user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: user_schema.UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=user_schema.UserRead)
async def read_users_me(current_user: user_schema.User = Depends(get_current_active_user)):
    return current_user


@app.post("/properties/", response_model=property_schema.PropertyRead)
async def create_property(
    property: property_schema.PropertyCreate,
    current_user: user_schema.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return crud.property.create_property(db=db, property=property, user_id=current_user.id)


@app.get("/properties/", response_model=List[property_schema.PropertyRead])
async def read_properties(
    skip: int = 0,
    limit: int = 100,
    current_user: user_schema.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    properties = crud.property.get_properties_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return properties


@app.get("/properties/{property_id}", response_model=property_schema.PropertyRead)
async def read_property(
    property_id: int,
    current_user: user_schema.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_property = crud.property.get_property(db, property_id=property_id, user_id=current_user.id)
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return db_property


@app.put("/properties/{property_id}", response_model=property_schema.PropertyRead)
async def update_property(
    property_id: int,
    property: property_schema.PropertyUpdate,
    current_user: user_schema.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_property = crud.property.update_property(
        db, property_id=property_id, property=property, user_id=current_user.id
    )
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return db_property


@app.delete("/properties/{property_id}")
async def delete_property(
    property_id: int,
    current_user: user_schema.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_property = crud.property.delete_property(db, property_id=property_id, user_id=current_user.id)
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"message": "Property deleted successfully"}