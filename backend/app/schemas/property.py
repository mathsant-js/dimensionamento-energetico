from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


def _clean_optional_string(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


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

    @field_validator("identification", "property_type", mode="before")
    @classmethod
    def validate_required_text_fields(cls, value):
        if value is None:
            raise ValueError("Este campo é obrigatório")
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Este campo é obrigatório")
        return value

    @field_validator("address", "city", "state", "orientation", "zipcode", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value):
        return _clean_optional_string(value)


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

    @field_validator("identification", "property_type", mode="before")
    @classmethod
    def validate_optional_required_text_fields(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Este campo é obrigatório")
        return value

    @field_validator("address", "city", "state", "orientation", "zipcode", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value):
        return _clean_optional_string(value)


class PropertyRead(PropertyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
