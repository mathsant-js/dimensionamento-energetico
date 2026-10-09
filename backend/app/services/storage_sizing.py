"""Funções puras para dimensionar o armazenamento opcional por baterias."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP, localcontext
from typing import Optional, Union

from app.schemas.pv_catalog import PVBattery


DecimalInput = Union[Decimal, int, str]
ENERGY_QUANTUM = Decimal("0.001")
HOURS_QUANTUM = Decimal("0.01")
MONEY_QUANTUM = Decimal("0.01")
DEFAULT_BATTERY_EFFICIENCY = Decimal("0.95")
ENERGY_UNIT = "kWh"
MONTHLY_ENERGY_UNIT = "kWh/mês"
DAILY_ENERGY_UNIT = "kWh/dia"
HOURS_UNIT = "h"
FRACTION_UNIT = "fração"
MONEY_UNIT = "BRL"


class StorageSizingValidationError(ValueError):
    """Erro de domínio estável, associado ao campo de entrada inválido."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True)
class StorageQuantity:
    value: Decimal
    unit: str


@dataclass(frozen=True)
class StorageSizingResult:
    storage_requested: bool
    reference_consumption: StorageQuantity
    period_days: int
    daily_consumption: StorageQuantity
    autonomy: StorageQuantity
    autonomy_energy: StorageQuantity
    battery_efficiency: StorageQuantity
    battery_catalog_id: Optional[str]
    battery_manufacturer: Optional[str]
    battery_model: Optional[str]
    depth_of_discharge: StorageQuantity
    unit_nominal_capacity: StorageQuantity
    required_nominal_capacity: StorageQuantity
    battery_quantity: int
    installed_nominal_capacity: StorageQuantity
    installed_deliverable_energy: StorageQuantity
    unit_price: StorageQuantity
    total_battery_cost: StorageQuantity


def _decimal(field: str, value: DecimalInput) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise StorageSizingValidationError(field, "use Decimal, inteiro ou texto decimal")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise StorageSizingValidationError(field, "deve ser um número decimal válido") from None
    if not result.is_finite():
        raise StorageSizingValidationError(field, "deve ser um número finito")
    return result


def _positive(field: str, value: DecimalInput) -> Decimal:
    result = _decimal(field, value)
    if result <= 0:
        raise StorageSizingValidationError(field, "deve ser maior que zero")
    return result


def _fraction(field: str, value: DecimalInput) -> Decimal:
    result = _positive(field, value)
    if result > 1:
        raise StorageSizingValidationError(field, "deve estar no intervalo (0, 1]")
    return result


def _autonomy(value: DecimalInput) -> Decimal:
    result = _decimal("autonomy_hours", value)
    if result < 0 or result > 24:
        raise StorageSizingValidationError(
            "autonomy_hours", "deve estar no intervalo [0, 24]"
        )
    return result


def _period_days(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StorageSizingValidationError("period_days", "deve ser um número inteiro")
    if value <= 0:
        raise StorageSizingValidationError("period_days", "deve ser maior que zero")
    return value


def _energy(value: Decimal, unit: str = ENERGY_UNIT) -> StorageQuantity:
    return StorageQuantity(
        value.quantize(ENERGY_QUANTUM, rounding=ROUND_HALF_UP), unit
    )


def _money(value: Decimal) -> StorageQuantity:
    return StorageQuantity(
        value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP), MONEY_UNIT
    )


def size_battery_storage(
    reference_consumption_kwh_month: DecimalInput,
    autonomy_hours: DecimalInput,
    battery: Optional[PVBattery] = None,
    period_days: int = 30,
    battery_efficiency: DecimalInput = DEFAULT_BATTERY_EFFICIENCY,
) -> StorageSizingResult:
    """Dimensiona BESS conforme o ADR-001, sem aplicar o DoD duas vezes.

    Autonomia zero representa o caminho sem armazenamento. Nesse caso nenhuma
    bateria é exigida e quantidade, capacidades instaladas e custo são zero.
    """

    consumption = _positive(
        "reference_consumption_kwh_month", reference_consumption_kwh_month
    )
    autonomy = _autonomy(autonomy_hours)
    days = _period_days(period_days)
    efficiency = _fraction("battery_efficiency", battery_efficiency)

    with localcontext() as context:
        context.prec = 28
        daily_consumption = consumption / Decimal(days)
        autonomy_energy = daily_consumption * autonomy / Decimal("24")

        if autonomy == 0:
            zero_energy = _energy(Decimal("0"))
            zero_money = _money(Decimal("0"))
            return StorageSizingResult(
                storage_requested=False,
                reference_consumption=_energy(consumption, MONTHLY_ENERGY_UNIT),
                period_days=days,
                daily_consumption=_energy(daily_consumption, DAILY_ENERGY_UNIT),
                autonomy=StorageQuantity(Decimal("0.00"), HOURS_UNIT),
                autonomy_energy=zero_energy,
                battery_efficiency=StorageQuantity(efficiency, FRACTION_UNIT),
                battery_catalog_id=None,
                battery_manufacturer=None,
                battery_model=None,
                depth_of_discharge=StorageQuantity(Decimal("0"), FRACTION_UNIT),
                unit_nominal_capacity=zero_energy,
                required_nominal_capacity=zero_energy,
                battery_quantity=0,
                installed_nominal_capacity=zero_energy,
                installed_deliverable_energy=zero_energy,
                unit_price=zero_money,
                total_battery_cost=zero_money,
            )

        if not isinstance(battery, PVBattery):
            raise StorageSizingValidationError(
                "battery", "deve ser uma bateria válida do catálogo quando a autonomia for maior que zero"
            )

        dod = _fraction("battery.dod_pct", battery.dod_pct / Decimal("100"))
        unit_capacity = _positive("battery.capacidade_kwh", battery.capacidade_kwh)
        unit_price = _positive("battery.preco_brl", battery.preco_brl)

        required_capacity = autonomy_energy / (dod * efficiency)
        quantity = int(
            (required_capacity / unit_capacity).to_integral_value(rounding=ROUND_CEILING)
        )
        installed_capacity = Decimal(quantity) * unit_capacity
        deliverable_energy = installed_capacity * dod * efficiency
        total_cost = Decimal(quantity) * unit_price

    if deliverable_energy < autonomy_energy:
        raise RuntimeError("invariante violada: energia instalada não atende à autonomia")

    return StorageSizingResult(
        storage_requested=True,
        reference_consumption=_energy(consumption, MONTHLY_ENERGY_UNIT),
        period_days=days,
        daily_consumption=_energy(daily_consumption, DAILY_ENERGY_UNIT),
        autonomy=StorageQuantity(
            autonomy.quantize(HOURS_QUANTUM, rounding=ROUND_HALF_UP), HOURS_UNIT
        ),
        autonomy_energy=_energy(autonomy_energy),
        battery_efficiency=StorageQuantity(efficiency, FRACTION_UNIT),
        battery_catalog_id=battery.id,
        battery_manufacturer=battery.fabricante,
        battery_model=battery.modelo,
        depth_of_discharge=StorageQuantity(dod, FRACTION_UNIT),
        unit_nominal_capacity=_energy(unit_capacity),
        required_nominal_capacity=_energy(required_capacity),
        battery_quantity=quantity,
        installed_nominal_capacity=_energy(installed_capacity),
        installed_deliverable_energy=_energy(deliverable_energy),
        unit_price=_money(unit_price),
        total_battery_cost=_money(total_cost),
    )
