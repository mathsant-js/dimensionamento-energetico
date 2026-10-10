"""Orquestração única do pré-dimensionamento usado pela API e persistência."""

from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi.encoders import jsonable_encoder

from app.schemas.pv import PVProposalCreate, PVProposalItemCreate, PVSimulationRequest
from app.schemas.pv_catalog import PVCatalog
from app.services.pv_budget import AdditionalCost, build_pv_bom
from app.services.pv_inverter_selection import require_budget_eligible_inverter, select_inverters
from app.services.pv_module_selection import compare_module_options
from app.services.pv_sizing import size_pv_generation
from app.services.storage_sizing import size_battery_storage


METHODOLOGY_VERSION = "ADR-001/v1"
DISCLAIMER = "Pré-dimensionamento acadêmico; não substitui projeto executivo, vistoria ou responsabilidade técnica."


class PVSimulationDomainError(ValueError):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def _find(records, catalog_id, field):
    if catalog_id is None:
        return None
    record = next((item for item in records if item.id == catalog_id), None)
    if record is None:
        raise PVSimulationDomainError(field, "item não encontrado no catálogo")
    return record


def simulate_pv_solution(
    property_id: int,
    consumption_kwh_month: Decimal,
    request: PVSimulationRequest,
    catalog: PVCatalog,
    consumption_calculated_at: Optional[datetime] = None,
):
    if consumption_kwh_month <= 0:
        raise PVSimulationDomainError(
            "reference_consumption_kwh_month",
            "a residência não possui consumo mensal calculável",
        )
    calculated_at = consumption_calculated_at or datetime.now(timezone.utc)
    calculation = size_pv_generation(
        consumption_kwh_month,
        request.target_offset_fraction,
        request.hsp_kwh_m2_day,
        request.period_days,
        request.performance_ratio,
    )
    comparison = compare_module_options(
        calculation.required_pv_power.value,
        catalog.modules,
        request.module_catalog_id,
    )
    module_option = comparison.selected or comparison.alternatives[0]
    module = _find(catalog.modules, module_option.catalog_id, "module_catalog_id")
    battery = _find(catalog.batteries, request.battery_catalog_id, "battery_catalog_id")
    storage = size_battery_storage(
        consumption_kwh_month,
        request.autonomy_hours,
        battery,
        request.period_days,
        request.battery_efficiency,
    )
    selection = select_inverters(module_option, module, catalog.inverters, storage)
    if not selection.compatible:
        raise PVSimulationDomainError(
            "inverter_catalog_id", "nenhum inversor compatível com a configuração calculada"
        )

    inverter_option = None
    budget = None
    inverter = None
    if request.inverter_catalog_id:
        inverter_option = require_budget_eligible_inverter(
            selection, request.inverter_catalog_id
        )
        inverter = _find(catalog.inverters, inverter_option.catalog_id, "inverter_catalog_id")
        budget = build_pv_bom(
            module_option,
            module,
            inverter_option,
            inverter,
            storage,
            battery,
            tuple(AdditionalCost(item.description, item.value_brl) for item in request.additional_costs),
        )

    return {
        "property_id": property_id,
        "consumption_calculated_at": calculated_at,
        "calculation": asdict(calculation),
        "module_alternatives": [asdict(item) for item in comparison.alternatives],
        "selected_module": asdict(module_option),
        "compatible_inverters": [asdict(item) for item in selection.compatible],
        "rejected_inverters": [asdict(item) for item in selection.rejected],
        "selected_inverter": asdict(inverter_option) if inverter_option else None,
        "storage": {
            key: value for key, value in asdict(storage).items()
            if key in {
                "storage_requested", "daily_consumption", "autonomy", "autonomy_energy",
                "battery_efficiency", "battery_catalog_id", "depth_of_discharge",
                "required_nominal_capacity", "battery_quantity", "installed_nominal_capacity",
                "installed_deliverable_energy", "total_battery_cost",
            }
        },
        "budget": asdict(budget) if budget else None,
        "methodology_version": METHODOLOGY_VERSION,
        "disclaimer": DISCLAIMER,
        "_objects": (module, module_option, inverter, inverter_option, battery, storage, budget),
    }


def proposal_from_simulation(request: PVSimulationRequest, result: dict) -> PVProposalCreate:
    module, module_option, inverter, inverter_option, battery, storage, budget = result["_objects"]
    if budget is None or inverter is None or inverter_option is None:
        raise PVSimulationDomainError(
            "inverter_catalog_id", "selecione um inversor compatível para salvar a proposta"
        )
    arrangement = jsonable_encoder([asdict(item) for item in inverter_option.arrangement])
    items = []
    for bom_item in budget.items:
        technical = {}
        strings = None
        diagnostics = None
        collected_at = None
        if bom_item.category == "module":
            technical = module.model_dump(mode="json")
            strings = arrangement
            collected_at = module.data_coleta
        elif bom_item.category == "inverter":
            technical = inverter.model_dump(mode="json")
            diagnostics = {"compatible": True, "arrangement": arrangement}
            collected_at = inverter.data_coleta
        elif bom_item.category == "battery" and battery is not None:
            technical = battery.model_dump(mode="json")
            collected_at = battery.data_coleta
        items.append(PVProposalItemCreate(
            item_type=bom_item.category,
            catalog_id=bom_item.catalog_id,
            manufacturer=bom_item.manufacturer,
            model=bom_item.model,
            description=bom_item.description,
            quantity=Decimal(bom_item.quantity),
            unit=bom_item.unit,
            unit_price_brl=bom_item.unit_price_brl,
            subtotal_brl=bom_item.subtotal_brl,
            supplier=bom_item.supplier,
            source_url=bom_item.source_url,
            collected_at=collected_at,
            technical_snapshot=technical,
            string_configuration=strings,
            compatibility_diagnostics=diagnostics,
        ))
    calc = result["calculation"]
    return PVProposalCreate(
        reference_consumption_kwh_month=calc["reference_consumption"]["value"],
        consumption_calculated_at=result["consumption_calculated_at"],
        hsp_kwh_m2_day=request.hsp_kwh_m2_day,
        hsp_source=request.hsp_source,
        hsp_source_date=request.hsp_source_date,
        target_offset_fraction=request.target_offset_fraction,
        period_days=request.period_days,
        performance_ratio=request.performance_ratio,
        target_energy_kwh=calc["target_energy"]["value"],
        required_pv_power_kwp=calc["required_pv_power"]["value"],
        installed_pv_power_kwp=module_option.installed_power_kwp,
        battery_requested=storage.storage_requested,
        autonomy_hours=request.autonomy_hours,
        battery_efficiency=request.battery_efficiency,
        required_battery_capacity_kwh=storage.required_nominal_capacity.value,
        installed_battery_capacity_kwh=storage.installed_nominal_capacity.value,
        modules_cost_brl=budget.modules_cost_brl,
        inverter_cost_brl=budget.inverter_cost_brl,
        batteries_cost_brl=budget.batteries_cost_brl,
        additional_cost_brl=budget.additional_cost_brl,
        equipment_cost_brl=budget.equipment_cost_brl,
        total_cost_brl=budget.total_cost_brl,
        methodology_version=METHODOLOGY_VERSION,
        disclaimer=DISCLAIMER,
        items=items,
    )
