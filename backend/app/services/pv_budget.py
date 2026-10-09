"""Montagem determinística da BOM de uma solução fotovoltaica elegível."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional, Sequence, Tuple, Union

from app.schemas.pv_catalog import PVBattery, PVInverter, PVModule
from app.services.pv_inverter_selection import CompatibleInverter
from app.services.pv_module_selection import PVModuleOption
from app.services.storage_sizing import StorageSizingResult


DecimalInput = Union[Decimal, int, str]
MONEY_QUANTUM = Decimal("0.01")
MONEY_UNIT = "BRL"


class PVBudgetValidationError(ValueError):
    """Erro de domínio estável associado ao campo inválido da BOM."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True)
class AdditionalCost:
    description: str
    value_brl: DecimalInput


@dataclass(frozen=True)
class BOMItem:
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


@dataclass(frozen=True)
class PVBudget:
    currency: str
    items: Tuple[BOMItem, ...]
    modules_cost_brl: Decimal
    inverter_cost_brl: Decimal
    batteries_cost_brl: Decimal
    additional_cost_brl: Decimal
    equipment_cost_brl: Decimal
    total_cost_brl: Decimal


def _money(field: str, value: DecimalInput, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise PVBudgetValidationError(field, "use Decimal, inteiro ou texto decimal")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise PVBudgetValidationError(field, "deve ser um valor monetário válido") from None
    if not result.is_finite() or result < 0 or (positive and result == 0):
        comparison = "maior que zero" if positive else "maior ou igual a zero"
        raise PVBudgetValidationError(field, f"deve ser finito e {comparison}")
    return result.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def _item(
    *,
    category: str,
    description: str,
    quantity: int,
    unit_price_brl: DecimalInput,
    unit: str = "unidade",
    catalog_id: Optional[str] = None,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    supplier: Optional[str] = None,
    source_url: Optional[str] = None,
) -> BOMItem:
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise PVBudgetValidationError(f"{category}.quantity", "deve ser um inteiro maior que zero")
    unit_price = _money(f"{category}.unit_price_brl", unit_price_brl)
    subtotal = _money(
        f"{category}.subtotal_brl", Decimal(quantity) * unit_price
    )
    return BOMItem(
        category=category,
        description=description,
        quantity=quantity,
        unit=unit,
        unit_price_brl=unit_price,
        subtotal_brl=subtotal,
        catalog_id=catalog_id,
        manufacturer=manufacturer,
        model=model,
        supplier=supplier,
        source_url=source_url,
    )


def _validate_component_snapshots(
    module_option: PVModuleOption,
    module: PVModule,
    inverter_option: CompatibleInverter,
    inverter: PVInverter,
) -> None:
    if not isinstance(module_option, PVModuleOption):
        raise PVBudgetValidationError("module_option", "deve ser uma opção dimensionada")
    if not isinstance(module, PVModule) or module_option.catalog_id != module.id:
        raise PVBudgetValidationError("module", "não corresponde à opção dimensionada")
    if not isinstance(inverter_option, CompatibleInverter):
        raise PVBudgetValidationError("inverter_option", "deve ser um inversor elegível")
    if not isinstance(inverter, PVInverter) or inverter_option.catalog_id != inverter.id:
        raise PVBudgetValidationError("inverter", "não corresponde ao inversor elegível")
    if _money("module.preco_brl", module.preco_brl, positive=True) != _money(
        "module_option.unit_price_brl", module_option.unit_price_brl, positive=True
    ):
        raise PVBudgetValidationError("module_option", "preço diverge do catálogo")
    if _money("inverter.preco_brl", inverter.preco_brl, positive=True) != _money(
        "inverter_option.unit_price_brl", inverter_option.unit_price_brl, positive=True
    ):
        raise PVBudgetValidationError("inverter_option", "preço diverge do catálogo")


def build_pv_bom(
    module_option: PVModuleOption,
    module: PVModule,
    inverter_option: CompatibleInverter,
    inverter: PVInverter,
    storage: StorageSizingResult,
    battery: Optional[PVBattery] = None,
    additional_costs: Sequence[AdditionalCost] = (),
) -> PVBudget:
    """Cria uma BOM somente a partir de resultados técnicos já validados.

    Todos os subtotais e totais são derivados novamente no servidor. Valores
    monetários usam ``Decimal`` e arredondamento ``ROUND_HALF_UP`` em centavos.
    """

    _validate_component_snapshots(module_option, module, inverter_option, inverter)
    if not isinstance(storage, StorageSizingResult):
        raise PVBudgetValidationError("storage", "deve ser um dimensionamento válido")

    items = [
        _item(
            category="module",
            description=f"Módulo fotovoltaico {module.fabricante} {module.modelo}",
            quantity=module_option.module_quantity,
            unit_price_brl=module.preco_brl,
            catalog_id=module.id,
            manufacturer=module.fabricante,
            model=module.modelo,
            supplier=module.fornecedor,
            source_url=module.url_fonte,
        ),
        _item(
            category="inverter",
            description=f"Inversor {inverter.fabricante} {inverter.modelo}",
            quantity=1,
            unit_price_brl=inverter.preco_brl,
            catalog_id=inverter.id,
            manufacturer=inverter.fabricante,
            model=inverter.modelo,
            supplier=inverter.fornecedor,
            source_url=inverter.url_fonte,
        ),
    ]

    if storage.storage_requested:
        if not inverter_option.battery_compatible:
            raise PVBudgetValidationError(
                "inverter_option", "armazenamento ativo exige inversor compatível com bateria"
            )
        if not isinstance(battery, PVBattery) or battery.id != storage.battery_catalog_id:
            raise PVBudgetValidationError("battery", "não corresponde ao dimensionamento")
        if storage.battery_quantity <= 0:
            raise PVBudgetValidationError("storage.battery_quantity", "deve ser maior que zero")
        if _money("battery.preco_brl", battery.preco_brl, positive=True) != _money(
            "storage.unit_price", storage.unit_price.value, positive=True
        ):
            raise PVBudgetValidationError("battery", "preço diverge do dimensionamento")
        items.append(_item(
            category="battery",
            description=f"Bateria {battery.fabricante} {battery.modelo}",
            quantity=storage.battery_quantity,
            unit_price_brl=battery.preco_brl,
            catalog_id=battery.id,
            manufacturer=battery.fabricante,
            model=battery.modelo,
            supplier=battery.fornecedor,
            source_url=battery.url_fonte,
        ))
    elif battery is not None:
        raise PVBudgetValidationError(
            "battery", "não deve ser informada quando não há armazenamento"
        )

    for index, cost in enumerate(additional_costs):
        field = f"additional_costs[{index}]"
        if not isinstance(cost, AdditionalCost):
            raise PVBudgetValidationError(field, "deve ser um custo adicional válido")
        description = cost.description.strip() if isinstance(cost.description, str) else ""
        if not description:
            raise PVBudgetValidationError(f"{field}.description", "não pode ser vazia")
        items.append(_item(
            category="additional",
            description=description,
            quantity=1,
            unit_price_brl=_money(f"{field}.value_brl", cost.value_brl),
            unit="serviço",
        ))

    immutable_items = tuple(items)
    modules_cost = sum(
        (item.subtotal_brl for item in immutable_items if item.category == "module"),
        Decimal("0.00"),
    )
    inverter_cost = sum(
        (item.subtotal_brl for item in immutable_items if item.category == "inverter"),
        Decimal("0.00"),
    )
    batteries_cost = sum(
        (item.subtotal_brl for item in immutable_items if item.category == "battery"),
        Decimal("0.00"),
    )
    additional_cost = sum(
        (item.subtotal_brl for item in immutable_items if item.category == "additional"),
        Decimal("0.00"),
    )
    equipment_cost = _money(
        "equipment_cost_brl", modules_cost + inverter_cost + batteries_cost
    )
    total_cost = _money("total_cost_brl", equipment_cost + additional_cost)

    # Defesa adicional contra uma futura alteração que introduza subtotais
    # inconsistentes: nenhuma soma recebida do cliente participa deste cálculo.
    for item in immutable_items:
        expected = _money(
            f"{item.category}.subtotal_brl",
            Decimal(item.quantity) * item.unit_price_brl,
        )
        if item.subtotal_brl != expected:
            raise RuntimeError("invariante violada: subtotal inconsistente na BOM")
    if total_cost != _money(
        "total_cost_brl", sum((item.subtotal_brl for item in immutable_items), Decimal("0"))
    ):
        raise RuntimeError("invariante violada: total inconsistente na BOM")

    return PVBudget(
        currency=MONEY_UNIT,
        items=immutable_items,
        modules_cost_brl=_money("modules_cost_brl", modules_cost),
        inverter_cost_brl=_money("inverter_cost_brl", inverter_cost),
        batteries_cost_brl=_money("batteries_cost_brl", batteries_cost),
        additional_cost_brl=_money("additional_cost_brl", additional_cost),
        equipment_cost_brl=equipment_cost,
        total_cost_brl=total_cost,
    )
