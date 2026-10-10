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


class PVAdditionalCostInput(BaseModel):
    description: str = Field(..., min_length=1, max_length=300)
    value_brl: Money = Field(..., ge=0)

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value):
        value = value.strip() if isinstance(value, str) else value
        if not value:
            raise ValueError("descrição do custo adicional não pode ser vazia")
        return value


class PVSimulationRequest(BaseModel):
    """Parâmetros controláveis; consumo, preços e especificações não vêm do cliente."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "hsp_kwh_m2_day": "5.10",
        "hsp_source": "Atlas Brasileiro de Energia Solar",
        "hsp_source_date": "2026-10-09",
        "target_offset_fraction": "0.80",
        "period_days": 30,
        "performance_ratio": "0.80",
        "module_catalog_id": "MOD-CAN-550-001",
        "inverter_catalog_id": "INV-GRO-3000-001",
        "autonomy_hours": "0",
        "battery_efficiency": "0.95",
        "additional_costs": [{"description": "Instalação", "value_brl": "1500.00"}],
    }})

    hsp_kwh_m2_day: Decimal = Field(..., gt=0)
    hsp_source: str = Field(..., min_length=1, max_length=500)
    hsp_source_date: date
    target_offset_fraction: Decimal = Field(Decimal("1"), gt=0, le=1)
    period_days: int = Field(30, gt=0, le=31)
    performance_ratio: Decimal = Field(Decimal("0.80"), gt=0, le=1)
    module_catalog_id: Optional[str] = Field(None, min_length=1, max_length=100)
    inverter_catalog_id: Optional[str] = Field(None, min_length=1, max_length=100)
    autonomy_hours: Decimal = Field(Decimal("0"), ge=0, le=24)
    battery_efficiency: Decimal = Field(Decimal("0.95"), gt=0, le=1)
    battery_catalog_id: Optional[str] = Field(None, min_length=1, max_length=100)
    additional_costs: List[PVAdditionalCostInput] = Field(default_factory=list, max_length=50)

    @field_validator("hsp_source", "module_catalog_id", "inverter_catalog_id", "battery_catalog_id", mode="before")
    @classmethod
    def strip_optional_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
        return value

    @model_validator(mode="after")
    def validate_storage_selection(self):
        if self.autonomy_hours > 0 and not self.battery_catalog_id:
            raise ValueError("battery_catalog_id é obrigatório quando autonomy_hours > 0")
        if self.autonomy_hours == 0 and self.battery_catalog_id is not None:
            raise ValueError("battery_catalog_id não deve ser informado quando autonomy_hours = 0")
        return self


class PVQuantityRead(BaseModel):
    value: Decimal
    unit: str


class PVModuleOptionRead(BaseModel):
    catalog_id: str
    manufacturer: str
    model: str
    module_power_wp: Decimal
    module_quantity: int
    installed_power_kwp: Decimal
    unit_price_brl: Decimal
    total_price_brl: Decimal


class PVStringArrangementRead(BaseModel):
    mppt_id: int
    module_quantity: int
    voc_v: Decimal
    vmp_v: Decimal


class PVCompatibleInverterRead(BaseModel):
    catalog_id: str
    manufacturer: str
    model: str
    inverter_type: str
    battery_compatible: bool
    unit_price_brl: Decimal
    installed_pv_power_w: Decimal
    arrangement: List[PVStringArrangementRead]


class PVIncompatibilityReasonRead(BaseModel):
    code: str
    message: str
    actual: Optional[Decimal] = None
    limit: Optional[Decimal] = None
    mppt_id: Optional[int] = None
    module_quantity: Optional[int] = None


class PVRejectedInverterRead(BaseModel):
    catalog_id: str
    manufacturer: str
    model: str
    reasons: List[PVIncompatibilityReasonRead]


class PVStorageRead(BaseModel):
    storage_requested: bool
    daily_consumption: PVQuantityRead
    autonomy: PVQuantityRead
    autonomy_energy: PVQuantityRead
    battery_efficiency: PVQuantityRead
    battery_catalog_id: Optional[str]
    depth_of_discharge: PVQuantityRead
    required_nominal_capacity: PVQuantityRead
    battery_quantity: int
    installed_nominal_capacity: PVQuantityRead
    installed_deliverable_energy: PVQuantityRead
    total_battery_cost: PVQuantityRead


class PVBOMItemRead(BaseModel):
    category: str
    description: str
    quantity: int
    unit: str
    unit_price_brl: Decimal
    subtotal_brl: Decimal
    catalog_id: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    supplier: Optional[str] = None
    source_url: Optional[str] = None


class PVBudgetRead(BaseModel):
    currency: str
    items: List[PVBOMItemRead]
    modules_cost_brl: Decimal
    inverter_cost_brl: Decimal
    batteries_cost_brl: Decimal
    additional_cost_brl: Decimal
    equipment_cost_brl: Decimal
    total_cost_brl: Decimal


class PVCalculationRead(BaseModel):
    reference_consumption: PVQuantityRead
    target_offset: PVQuantityRead
    hsp: PVQuantityRead
    period_days: PVQuantityRead
    performance_ratio: PVQuantityRead
    target_energy: PVQuantityRead
    required_pv_power: PVQuantityRead


class PVSimulationRead(BaseModel):
    property_id: int
    consumption_calculated_at: datetime
    calculation: PVCalculationRead
    module_alternatives: List[PVModuleOptionRead]
    selected_module: PVModuleOptionRead
    compatible_inverters: List[PVCompatibleInverterRead]
    rejected_inverters: List[PVRejectedInverterRead]
    selected_inverter: Optional[PVCompatibleInverterRead]
    storage: PVStorageRead
    budget: Optional[PVBudgetRead]
    methodology_version: str
    disclaimer: str
