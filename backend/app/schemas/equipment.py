from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Equipment Schemas
class EquipmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    power_watts: float = Field(..., gt=0)

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentRead(EquipmentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# PropertyEquipment Schemas
class PropertyEquipmentBase(BaseModel):
    equipment_id: int
    quantity: int = Field(default=1, ge=1)
    hours_per_day: float = Field(..., ge=0, le=24)

class PropertyEquipmentCreate(PropertyEquipmentBase):
    pass

class PropertyEquipmentUpdate(BaseModel):
    quantity: Optional[int] = Field(None, ge=1)
    hours_per_day: Optional[float] = Field(None, ge=0, le=24)

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
