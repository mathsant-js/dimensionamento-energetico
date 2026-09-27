from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PropertyBase(BaseModel):
    identification: str = Field(..., min_length=2, max_length=200)  # Nome/Identificação do imóvel
    property_type: str = Field(..., min_length=2, max_length=50)  # Tipo do imóvel (obrigatório)
    address: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zipcode: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    built_area: Optional[float] = Field(None, gt=0)
    roof_area: Optional[float] = Field(None, ge=0)
    orientation: Optional[str] = Field(None, max_length=20)
    tilt_angle: Optional[float] = Field(None, ge=0, le=90)

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(BaseModel):
    identification: Optional[str] = Field(None, min_length=2, max_length=200)  # Nome/Identificação do imóvel
    property_type: Optional[str] = Field(None, min_length=2, max_length=50)  # Tipo do imóvel
    address: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zipcode: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    built_area: Optional[float] = Field(None, gt=0)
    roof_area: Optional[float] = Field(None, ge=0)
    orientation: Optional[str] = Field(None, max_length=20)
    tilt_angle: Optional[float] = Field(None, ge=0, le=90)

class PropertyRead(PropertyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True