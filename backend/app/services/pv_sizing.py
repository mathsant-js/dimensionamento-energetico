"""Funções puras para o pré-dimensionamento da geração fotovoltaica."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from typing import Union


DecimalInput = Union[Decimal, int, str]
ENERGY_QUANTUM = Decimal("0.001")
POWER_QUANTUM = Decimal("0.000001")
ENERGY_UNIT = "kWh/mês"
POWER_UNIT = "kWp"
HSP_UNIT = "kWh/m²/dia"
OFFSET_UNIT = "fração"
PR_UNIT = "fração"
DAYS_UNIT = "dias"


class PVSizingValidationError(ValueError):
    """Erro de domínio estável, associado ao campo de entrada inválido."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True)
class Quantity:
    value: Decimal
    unit: str


@dataclass(frozen=True)
class PVSizingResult:
    reference_consumption: Quantity
    target_offset: Quantity
    hsp: Quantity
    period_days: Quantity
    performance_ratio: Quantity
    target_energy: Quantity
    required_pv_power: Quantity


def _decimal(field: str, value: DecimalInput) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise PVSizingValidationError(field, "use Decimal, inteiro ou texto decimal")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise PVSizingValidationError(field, "deve ser um número decimal válido") from None
    if not result.is_finite():
        raise PVSizingValidationError(field, "deve ser um número finito")
    return result


def _positive(field: str, value: DecimalInput) -> Decimal:
    result = _decimal(field, value)
    if result <= 0:
        raise PVSizingValidationError(field, "deve ser maior que zero")
    return result


def _fraction(field: str, value: DecimalInput) -> Decimal:
    result = _positive(field, value)
    if result > 1:
        raise PVSizingValidationError(field, "deve estar no intervalo (0, 1]")
    return result


def _period_days(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PVSizingValidationError("period_days", "deve ser um número inteiro")
    if value <= 0:
        raise PVSizingValidationError("period_days", "deve ser maior que zero")
    return value


def calculate_target_energy(
    reference_consumption_kwh_month: DecimalInput,
    target_offset_fraction: DecimalInput,
) -> Decimal:
    """Calcula E_FV = C_m × f, em kWh/mês."""

    consumption = _positive("reference_consumption_kwh_month", reference_consumption_kwh_month)
    offset = _fraction("target_offset_fraction", target_offset_fraction)
    with localcontext() as context:
        context.prec = 28
        return (consumption * offset).quantize(ENERGY_QUANTUM, rounding=ROUND_HALF_UP)


def calculate_required_pv_power(
    target_energy_kwh_month: DecimalInput,
    hsp_hours_day: DecimalInput,
    period_days: int = 30,
    performance_ratio: DecimalInput = Decimal("0.80"),
) -> Decimal:
    """Calcula P_FV = E_FV / (HSP × D × PR), em kWp."""

    energy = _positive("target_energy_kwh_month", target_energy_kwh_month)
    hsp = _positive("hsp_hours_day", hsp_hours_day)
    days = _period_days(period_days)
    ratio = _fraction("performance_ratio", performance_ratio)
    with localcontext() as context:
        context.prec = 28
        return (energy / (hsp * Decimal(days) * ratio)).quantize(
            POWER_QUANTUM, rounding=ROUND_HALF_UP
        )


def size_pv_generation(
    reference_consumption_kwh_month: DecimalInput,
    target_offset_fraction: DecimalInput,
    hsp_hours_day: DecimalInput,
    period_days: int = 30,
    performance_ratio: DecimalInput = Decimal("0.80"),
) -> PVSizingResult:
    """Valida entradas e devolve o cálculo completo, reproduzível e com unidades."""

    consumption = _positive("reference_consumption_kwh_month", reference_consumption_kwh_month)
    offset = _fraction("target_offset_fraction", target_offset_fraction)
    hsp = _positive("hsp_hours_day", hsp_hours_day)
    days = _period_days(period_days)
    ratio = _fraction("performance_ratio", performance_ratio)
    energy = calculate_target_energy(consumption, offset)
    power = calculate_required_pv_power(energy, hsp, days, ratio)

    return PVSizingResult(
        reference_consumption=Quantity(consumption, ENERGY_UNIT),
        target_offset=Quantity(offset, OFFSET_UNIT),
        hsp=Quantity(hsp, HSP_UNIT),
        period_days=Quantity(Decimal(days), DAYS_UNIT),
        performance_ratio=Quantity(ratio, PR_UNIT),
        target_energy=Quantity(energy, ENERGY_UNIT),
        required_pv_power=Quantity(power, POWER_UNIT),
    )
