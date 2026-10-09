from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Money = Decimal
HSP_UNIT = "kWh/m²/dia"


class PropertySolarResourceUpsert(BaseModel):
    hsp_kwh_m2_day: Decimal = Field(..., gt=0, max_digits=8, decimal_places=3)
    unit: Literal["kWh/m²/dia"] = HSP_UNIT
    source: str = Field(..., min_length=1, max_length=500)
    source_date: date
    # Location-based sources will be added only when a trusted provider is configured.
    acquisition_mode: Literal["manual"] = "manual"

    @field_validator("source", mode="before")
    @classmethod
    def strip_source(cls, value):
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("origem do HSP não pode ser vazia")
        return value


class PropertySolarResourceRead(PropertySolarResourceUpsert):
    model_config = ConfigDict(from_attributes=True)

    id: int
    property_id: int
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_latitude: Optional[Decimal] = None
    location_longitude: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime


class PVProposalItemCreate(BaseModel):
    item_type: Literal["module", "inverter", "battery", "additional"]
    catalog_id: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=150)
    model: Optional[str] = Field(None, max_length=150)
    description: str = Field(..., min_length=1, max_length=300)
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=30)
    unit_price_brl: Money = Field(..., ge=0)
    subtotal_brl: Money = Field(..., ge=0)
    supplier: Optional[str] = Field(None, max_length=200)
    source_url: Optional[str] = None
    collected_at: Optional[date] = None
    technical_snapshot: Dict[str, Any] = Field(default_factory=dict)
    string_configuration: Optional[List[Dict[str, Any]]] = None
    compatibility_diagnostics: Optional[Dict[str, Any]] = None

    @field_validator("description", "unit", mode="before")
    @classmethod
    def strip_required_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("campo obrigatório não pode ser vazio")
        return value

    @model_validator(mode="after")
    def subtotal_matches_quantity(self):
        expected = (self.quantity * self.unit_price_brl).quantize(Decimal("0.01"))
        if self.subtotal_brl.quantize(Decimal("0.01")) != expected:
            raise ValueError("subtotal_brl deve ser igual a quantity × unit_price_brl")
        return self


class PVProposalCreate(BaseModel):
    status: str = Field("draft", min_length=1, max_length=30)
    reference_consumption_kwh_month: Decimal = Field(..., gt=0)
    consumption_calculated_at: datetime
    hsp_kwh_m2_day: Decimal = Field(..., gt=0)
    hsp_unit: Literal["kWh/m²/dia"] = HSP_UNIT
    hsp_source: str = Field(..., min_length=1)
    hsp_source_date: date
    hsp_is_manual: bool = True
    target_offset_fraction: Decimal = Field(..., gt=0, le=1)
    period_days: int = Field(30, gt=0)
    performance_ratio: Decimal = Field(..., gt=0, le=1)
    target_energy_kwh: Decimal = Field(..., ge=0)
    required_pv_power_kwp: Decimal = Field(..., gt=0)
    installed_pv_power_kwp: Decimal = Field(..., gt=0)
    battery_requested: bool = False
    autonomy_hours: Decimal = Field(Decimal("0"), ge=0, le=24)
    battery_efficiency: Decimal = Field(Decimal("0.95"), gt=0, le=1)
    required_battery_capacity_kwh: Decimal = Field(Decimal("0"), ge=0)
    installed_battery_capacity_kwh: Decimal = Field(Decimal("0"), ge=0)
    modules_cost_brl: Money = Field(Decimal("0"), ge=0)
    inverter_cost_brl: Money = Field(Decimal("0"), ge=0)
    batteries_cost_brl: Money = Field(Decimal("0"), ge=0)
    additional_cost_brl: Money = Field(Decimal("0"), ge=0)
    equipment_cost_brl: Money = Field(Decimal("0"), ge=0)
    total_cost_brl: Money = Field(Decimal("0"), ge=0)
    methodology_version: str = Field(..., min_length=1, max_length=50)
    disclaimer: str = Field(..., min_length=1)
    items: List[PVProposalItemCreate] = Field(default_factory=list)

    @field_validator("hsp_source", "methodology_version", "disclaimer", mode="before")
    @classmethod
    def strip_required_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("campo obrigatório não pode ser vazio")
        return value

    @model_validator(mode="after")
    def validate_storage_consistency(self):
        if not self.battery_requested:
            if any(
                value != 0
                for value in (
                    self.autonomy_hours,
                    self.required_battery_capacity_kwh,
                    self.installed_battery_capacity_kwh,
                    self.batteries_cost_brl,
                )
            ):
                raise ValueError("sem bateria, autonomia, capacidades e custo de bateria devem ser zero")
        elif self.autonomy_hours <= 0:
            raise ValueError("autonomy_hours deve ser maior que zero quando battery_requested=true")
        return self


class PVProposalItemRead(PVProposalItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    proposal_id: int
    created_at: datetime


class PVProposalRead(PVProposalCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    property_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    items: List[PVProposalItemRead]
