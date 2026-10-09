"""Dimensionamento e comparação de módulos fotovoltaicos do catálogo."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP, localcontext
from typing import Optional, Sequence, Tuple, Union

from app.schemas.pv_catalog import PVModule


DecimalInput = Union[Decimal, int, str]
POWER_QUANTUM = Decimal("0.000001")
MONEY_QUANTUM = Decimal("0.01")


class PVModuleSelectionError(ValueError):
    """Erro de domínio estável associado ao campo inválido."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True)
class PVModuleOption:
    catalog_id: str
    manufacturer: str
    model: str
    module_power_wp: Decimal
    module_quantity: int
    installed_power_kwp: Decimal
    unit_price_brl: Decimal
    total_price_brl: Decimal


@dataclass(frozen=True)
class PVModuleComparison:
    required_pv_power_kwp: Decimal
    alternatives: Tuple[PVModuleOption, ...]
    selected: Optional[PVModuleOption]


def _positive_decimal(field: str, value: DecimalInput) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise PVModuleSelectionError(field, "use Decimal, inteiro ou texto decimal")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise PVModuleSelectionError(field, "deve ser um número decimal válido") from None
    if not result.is_finite() or result <= 0:
        raise PVModuleSelectionError(field, "deve ser maior que zero e finito")
    return result


def size_module_option(
    required_pv_power_kwp: DecimalInput,
    module: PVModule,
) -> PVModuleOption:
    """Dimensiona uma opção com ceil(P_FV × 1000 / P_módulo)."""

    required_power = _positive_decimal("required_pv_power_kwp", required_pv_power_kwp)
    if not isinstance(module, PVModule):
        raise PVModuleSelectionError("module", "deve ser um módulo válido do catálogo")

    with localcontext() as context:
        context.prec = 28
        quantity = int(
            (required_power * Decimal("1000") / module.potencia_wp).to_integral_value(
                rounding=ROUND_CEILING
            )
        )
        installed_power = (
            Decimal(quantity) * module.potencia_wp / Decimal("1000")
        ).quantize(POWER_QUANTUM, rounding=ROUND_HALF_UP)
        total_price = (Decimal(quantity) * module.preco_brl).quantize(
            MONEY_QUANTUM, rounding=ROUND_HALF_UP
        )

    return PVModuleOption(
        catalog_id=module.id,
        manufacturer=module.fabricante,
        model=module.modelo,
        module_power_wp=module.potencia_wp,
        module_quantity=quantity,
        installed_power_kwp=installed_power,
        unit_price_brl=module.preco_brl.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP),
        total_price_brl=total_price,
    )


def compare_module_options(
    required_pv_power_kwp: DecimalInput,
    modules: Sequence[PVModule],
    selected_module_id: Optional[str] = None,
) -> PVModuleComparison:
    """Dimensiona o catálogo e, opcionalmente, seleciona uma alternativa pelo ID."""

    required_power = _positive_decimal("required_pv_power_kwp", required_pv_power_kwp)
    if not modules:
        raise PVModuleSelectionError("modules", "catálogo de módulos vazio")

    options = tuple(size_module_option(required_power, module) for module in modules)
    alternatives = tuple(
        sorted(
            options,
            key=lambda option: (
                option.total_price_brl,
                option.installed_power_kwp,
                option.catalog_id,
            ),
        )
    )

    selected = None
    if selected_module_id is not None:
        normalized_id = selected_module_id.strip() if isinstance(selected_module_id, str) else ""
        if not normalized_id:
            raise PVModuleSelectionError("selected_module_id", "não pode ser vazio")
        selected = next(
            (option for option in alternatives if option.catalog_id == normalized_id),
            None,
        )
        if selected is None:
            raise PVModuleSelectionError(
                "selected_module_id", "módulo não encontrado no catálogo"
            )

    return PVModuleComparison(
        required_pv_power_kwp=required_power.quantize(
            POWER_QUANTUM, rounding=ROUND_HALF_UP
        ),
        alternatives=alternatives,
        selected=selected,
    )
