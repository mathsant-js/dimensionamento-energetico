from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


def _clean_string(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


# Equipment Schemas
class EquipmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    power_watts: float = Field(..., gt=0)

    @field_validator("name", "category", mode="before")
    @classmethod
    def validate_required_text_fields(cls, value):
        if value is None:
            raise ValueError("Este campo é obrigatório")
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Este campo é obrigatório")
        return value


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentRead(EquipmentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# PropertyEquipment Schemas
class PropertyEquipmentBase(BaseModel):
    equipment_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1)
    hours_per_day: float = Field(..., ge=0, le=24)

    @field_validator("hours_per_day")
    @classmethod
    def validate_hours_per_day(cls, value):
        if value is None:
            raise ValueError("Este campo é obrigatório")
        if value < 0 or value > 24:
            raise ValueError("O tempo de uso diário deve estar entre 0 e 24 horas")
        return value


class PropertyEquipmentCreate(PropertyEquipmentBase):
    pass


class PropertyEquipmentUpdate(BaseModel):
    quantity: int = Field(..., ge=1)
    hours_per_day: float = Field(..., ge=0, le=24)

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value):
        if value <= 0:
            raise ValueError("A quantidade deve ser maior que zero")
        return value

    @field_validator("hours_per_day")
    @classmethod
    def validate_hours_per_day(cls, value):
        if value < 0 or value > 24:
            raise ValueError("O tempo de uso diário deve estar entre 0 e 24 horas")
        return value


class PropertyEquipmentRead(PropertyEquipmentBase):
    id: int
    property_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Extended PropertyEquipment with Equipment details
class PropertyEquipmentWithDetailsRead(PropertyEquipmentRead):
    equipment: EquipmentRead


# Consumption Report Item
class ConsumptionReportItem(BaseModel):
    id: int
    equipment_name: str
    power_watts: float
    quantity: int
    hours_per_day: float
    monthly_consumption_kwh: float  # Calculated: (power_watts * quantity * hours_per_day * 30) / 1000


class ConsumptionReport(BaseModel):
    property_id: int
    property_name: str
    property_type: str
    items: List[ConsumptionReportItem]
    total_monthly_consumption_kwh: float
    created_at: datetime
