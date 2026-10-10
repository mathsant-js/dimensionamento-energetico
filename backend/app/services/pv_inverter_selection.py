"""Seleção determinística de inversores e arranjos de strings fotovoltaicas."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Sequence, Tuple

from app.schemas.pv_catalog import PVInverter, PVModule
from app.services.pv_module_selection import PVModuleOption
from app.services.storage_sizing import StorageSizingResult


VOLTAGE_QUANTUM = Decimal("0.001")
POWER_QUANTUM = Decimal("0.001")
MONEY_QUANTUM = Decimal("0.01")


class PVInverterSelectionError(ValueError):
    """Erro de domínio estável associado ao campo inválido."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True)
class PVStringArrangement:
    mppt_id: int
    module_quantity: int
    voc_v: Decimal
    vmp_v: Decimal


@dataclass(frozen=True)
class IncompatibilityReason:
    code: str
    message: str
    actual: Optional[Decimal] = None
    limit: Optional[Decimal] = None
    mppt_id: Optional[int] = None
    module_quantity: Optional[int] = None


@dataclass(frozen=True)
class CompatibleInverter:
    catalog_id: str
    manufacturer: str
    model: str
    inverter_type: str
    battery_compatible: bool
    unit_price_brl: Decimal
    installed_pv_power_w: Decimal
    arrangement: Tuple[PVStringArrangement, ...]


@dataclass(frozen=True)
class RejectedInverter:
    catalog_id: str
    manufacturer: str
    model: str
    reasons: Tuple[IncompatibilityReason, ...]


@dataclass(frozen=True)
class PVInverterSelection:
    compatible: Tuple[CompatibleInverter, ...]
    rejected: Tuple[RejectedInverter, ...]


def _arrangement(module_count: int, string_count: int, module: PVModule):
    """Distribui N módulos de modo equilibrado e lexicograficamente decrescente."""

    base, remainder = divmod(module_count, string_count)
    quantities = tuple(base + (1 if index < remainder else 0) for index in range(string_count))
    return tuple(
        PVStringArrangement(
            mppt_id=index + 1,
            module_quantity=quantity,
            voc_v=(Decimal(quantity) * module.voc_v).quantize(
                VOLTAGE_QUANTUM, rounding=ROUND_HALF_UP
            ),
            vmp_v=(Decimal(quantity) * module.vmp_v).quantize(
                VOLTAGE_QUANTUM, rounding=ROUND_HALF_UP
            ),
        )
        for index, quantity in enumerate(quantities)
    )


def _voltage_reasons(
    arrangement: Tuple[PVStringArrangement, ...], inverter: PVInverter
) -> Tuple[IncompatibilityReason, ...]:
    reasons = []
    for string in arrangement:
        common = {"mppt_id": string.mppt_id, "module_quantity": string.module_quantity}
        if string.voc_v > inverter.tensao_max_entrada_v:
            reasons.append(IncompatibilityReason(
                code="VOC_ABOVE_MAXIMUM",
                message="Voc da string excede a tensão máxima de entrada do inversor",
                actual=string.voc_v,
                limit=inverter.tensao_max_entrada_v,
                **common,
            ))
        if string.vmp_v < inverter.faixa_mppt_min_v:
            reasons.append(IncompatibilityReason(
                code="VMP_BELOW_MPPT_MINIMUM",
                message="Vmp da string está abaixo do limite inferior do MPPT",
                actual=string.vmp_v,
                limit=inverter.faixa_mppt_min_v,
                **common,
            ))
        if string.vmp_v > inverter.faixa_mppt_max_v:
            reasons.append(IncompatibilityReason(
                code="VMP_ABOVE_MPPT_MAXIMUM",
                message="Vmp da string excede o limite superior do MPPT",
                actual=string.vmp_v,
                limit=inverter.faixa_mppt_max_v,
                **common,
            ))
    return tuple(reasons)


def _select_arrangement(module_count: int, module: PVModule, inverter: PVInverter):
    last_reasons: Tuple[IncompatibilityReason, ...] = ()
    for string_count in range(1, min(module_count, inverter.numero_mppt) + 1):
        candidate = _arrangement(module_count, string_count, module)
        reasons = _voltage_reasons(candidate, inverter)
        if not reasons:
            return candidate, ()
        last_reasons = reasons
    # A última tentativa usa o maior número de MPPTs e é o diagnóstico da
    # configuração com menor tensão por string (a mais próxima de ser viável).
    return None, last_reasons


def select_inverters(
    module_option: PVModuleOption,
    module: PVModule,
    inverters: Sequence[PVInverter],
    storage: Optional[StorageSizingResult] = None,
) -> PVInverterSelection:
    """Valida a arquitetura completa e ordena por preço só os elegíveis.

    Quando ``storage`` representa autonomia ativa, inversores sem suporte a
    bateria são rejeitados depois das verificações elétricas. Autonomia zero
    mantém os inversores on-grid elegíveis, conforme o ADR-001.
    """

    if not isinstance(module_option, PVModuleOption):
        raise PVInverterSelectionError("module_option", "deve ser uma opção dimensionada")
    if not isinstance(module, PVModule):
        raise PVInverterSelectionError("module", "deve ser um módulo válido do catálogo")
    if module_option.catalog_id != module.id:
        raise PVInverterSelectionError("module", "não corresponde à opção dimensionada")
    if not inverters:
        raise PVInverterSelectionError("inverters", "catálogo de inversores vazio")
    if storage is not None and not isinstance(storage, StorageSizingResult):
        raise PVInverterSelectionError(
            "storage", "deve ser um resultado de dimensionamento de armazenamento"
        )

    installed_power_w = (
        Decimal(module_option.module_quantity) * module.potencia_wp
    ).quantize(POWER_QUANTUM, rounding=ROUND_HALF_UP)
    compatible = []
    rejected = []

    for inverter in inverters:
        if not isinstance(inverter, PVInverter):
            raise PVInverterSelectionError("inverters", "contém inversor inválido")

        if installed_power_w > inverter.potencia_max_fv_w:
            rejected.append(RejectedInverter(
                catalog_id=inverter.id,
                manufacturer=inverter.fabricante,
                model=inverter.modelo,
                reasons=(IncompatibilityReason(
                    code="PV_POWER_ABOVE_MAXIMUM",
                    message="potência FV instalada excede a capacidade máxima do inversor",
                    actual=installed_power_w,
                    limit=inverter.potencia_max_fv_w,
                ),),
            ))
            continue

        arrangement, reasons = _select_arrangement(
            module_option.module_quantity, module, inverter
        )
        if arrangement is None:
            rejected.append(RejectedInverter(
                catalog_id=inverter.id,
                manufacturer=inverter.fabricante,
                model=inverter.modelo,
                reasons=reasons,
            ))
            continue

        if storage is not None and storage.storage_requested and not inverter.compativel_bateria:
            rejected.append(RejectedInverter(
                catalog_id=inverter.id,
                manufacturer=inverter.fabricante,
                model=inverter.modelo,
                reasons=(IncompatibilityReason(
                    code="STORAGE_REQUIRES_BATTERY_COMPATIBLE_INVERTER",
                    message=(
                        "armazenamento ativo exige inversor compatível com bateria"
                    ),
                ),),
            ))
            continue

        compatible.append(CompatibleInverter(
            catalog_id=inverter.id,
            manufacturer=inverter.fabricante,
            model=inverter.modelo,
            inverter_type=inverter.tipo,
            battery_compatible=inverter.compativel_bateria,
            unit_price_brl=inverter.preco_brl.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP),
            installed_pv_power_w=installed_power_w,
            arrangement=arrangement,
        ))

    return PVInverterSelection(
        compatible=tuple(sorted(
            compatible, key=lambda item: (item.unit_price_brl, item.catalog_id)
        )),
        rejected=tuple(rejected),
    )


def require_budget_eligible_inverter(
    selection: PVInverterSelection,
    inverter_catalog_id: str,
) -> CompatibleInverter:
    """Retorna uma opção elegível ou bloqueia o orçamento incompatível."""

    if not isinstance(selection, PVInverterSelection):
        raise PVInverterSelectionError("selection", "deve ser uma seleção de inversores")
    normalized_id = (
        inverter_catalog_id.strip() if isinstance(inverter_catalog_id, str) else ""
    )
    if not normalized_id:
        raise PVInverterSelectionError("inverter_catalog_id", "não pode ser vazio")

    eligible = next(
        (item for item in selection.compatible if item.catalog_id == normalized_id),
        None,
    )
    if eligible is not None:
        return eligible

    rejected = next(
        (item for item in selection.rejected if item.catalog_id == normalized_id),
        None,
    )
    if rejected is not None:
        reason_codes = ", ".join(reason.code for reason in rejected.reasons)
        raise PVInverterSelectionError(
            "inverter_catalog_id",
            f"inversor incompatível não pode ser orçado ({reason_codes})",
        )
    raise PVInverterSelectionError(
        "inverter_catalog_id", "inversor não pertence ao resultado da seleção"
    )
