from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Generator, List
from datetime import timedelta
from typing import List

from .database import Base, engine, SessionLocal
from .crud import property as property_crud, user as user_crud, equipment as equipment_crud
from . import schemas, models
from .seed import seed_equipments
from .auth import authenticate_user, create_access_token, get_current_active_user
from .schemas import user as user_schema, property as property_schema, equipment as equipment_schema
from .schemas.user import Token
from .core.config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

# Seed equipments
db = SessionLocal()
try:
    seed_equipments(db)
finally:
    db.close()

# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/users/", response_model=user_schema.UserRead)
async def register_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Create user (password will be hashed inside CRUD)
    db_user = user_crud.create_user(db=db, user=user)
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
async def read_users_me(current_user: user_schema.UserRead = Depends(get_current_active_user)):
    return current_user


@app.post("/properties/", response_model=property_schema.PropertyRead)
async def create_property(
    property: property_schema.PropertyCreate,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return property_crud.create_property(db=db, property=property, user_id=current_user.id)


@app.get("/properties/", response_model=List[property_schema.PropertyRead])
async def read_properties(
    skip: int = 0,
    limit: int = 100,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    properties = property_crud.get_properties_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return properties


@app.get("/properties/{property_id}", response_model=property_schema.PropertyRead)
async def read_property(
    property_id: int,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_property = property_crud.get_property(db, property_id=property_id, user_id=current_user.id)
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return db_property


@app.put("/properties/{property_id}", response_model=property_schema.PropertyRead)
async def update_property(
    property_id: int,
    property: property_schema.PropertyUpdate,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_property = property_crud.update_property(
        db, property_id=property_id, property=property, user_id=current_user.id
    )
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return db_property


@app.delete("/properties/{property_id}")
async def delete_property(
    property_id: int,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_property = property_crud.delete_property(db, property_id=property_id, user_id=current_user.id)
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"message": "Property deleted successfully"}


# Equipment Endpoints

@app.get("/equipments/", response_model=List[equipment_schema.EquipmentRead])
async def read_equipments(
    skip: int = 0,
    limit: int = 100,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    equipments = equipment_crud.get_all_equipments(db, skip=skip, limit=limit)
    return equipments


@app.post("/equipments/", response_model=equipment_schema.EquipmentRead)
async def create_equipment_endpoint(
    equipment: equipment_schema.EquipmentCreate,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return equipment_crud.create_equipment(db, equipment)


# Property Equipment (Consumption) Endpoints

@app.get("/properties/{property_id}/equipments/", response_model=List[equipment_schema.PropertyEquipmentWithDetailsRead])
async def read_property_equipments(
    property_id: int,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify property belongs to user
    db_property = property_crud.get_property(db, property_id=property_id, user_id=current_user.id)
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return equipment_crud.get_property_equipments(db, property_id=property_id, user_id=current_user.id)


@app.post("/properties/{property_id}/equipments/", response_model=equipment_schema.PropertyEquipmentRead)
async def create_property_equipment(
    property_id: int,
    property_equipment: equipment_schema.PropertyEquipmentCreate,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify property belongs to user
    db_property = property_crud.get_property(db, property_id=property_id, user_id=current_user.id)
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Verify equipment exists
    equipment = equipment_crud.get_equipment(db, property_equipment.equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    created = equipment_crud.create_property_equipment(db, property_id, property_equipment, user_id=current_user.id)
    if created is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return created


@app.put("/properties/{property_id}/equipments/{equipment_id}", response_model=equipment_schema.PropertyEquipmentRead)
async def update_property_equipment(
    property_id: int,
    equipment_id: int,
    property_equipment: equipment_schema.PropertyEquipmentUpdate,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify property belongs to user
    db_property = property_crud.get_property(db, property_id=property_id, user_id=current_user.id)
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Find and update the property equipment
    db_property_equipment = db.query(models.PropertyEquipment).filter(
        models.PropertyEquipment.id == equipment_id,
        models.PropertyEquipment.property_id == property_id
    ).first()
    
    if db_property_equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found for this property")
    
    updated = equipment_crud.update_property_equipment(db, equipment_id, property_equipment, user_id=current_user.id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Equipment not found for this property")
    return updated


@app.delete("/properties/{property_id}/equipments/{equipment_id}")
async def delete_property_equipment(
    property_id: int,
    equipment_id: int,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify property belongs to user
    db_property = property_crud.get_property(db, property_id=property_id, user_id=current_user.id)
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Find and delete the property equipment
    db_property_equipment = db.query(models.PropertyEquipment).filter(
        models.PropertyEquipment.id == equipment_id,
        models.PropertyEquipment.property_id == property_id
    ).first()
    
    if db_property_equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found for this property")
    
    deleted = equipment_crud.delete_property_equipment(db, equipment_id, user_id=current_user.id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Equipment not found for this property")
    return {"message": "Equipment removed from property successfully"}


# Consumption Report Endpoint

@app.get("/properties/{property_id}/consumption-report", response_model=equipment_schema.ConsumptionReport)
async def get_property_consumption_report(
    property_id: int,
    current_user: user_schema.UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    report = equipment_crud.get_consumption_report(db, property_id=property_id, user_id=current_user.id)
    if report is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return report
