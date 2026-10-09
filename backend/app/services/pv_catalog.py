"""Carregamento central, estrito e atômico dos catálogos FV em CSV."""

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, TypeVar
from urllib.parse import urlparse

from app.schemas.pv_catalog import PVBattery, PVCatalog, PVInverter, PVModule


DEFAULT_CATALOG_DIR = Path(__file__).resolve().parents[2] / "data" / "pv"

MODULE_HEADER = (
    "id", "fabricante", "modelo", "potencia_wp", "voc_v", "isc_a", "vmp_v",
    "imp_a", "eficiencia_pct", "preco_brl", "fornecedor", "data_coleta", "url_fonte",
)
INVERTER_HEADER = (
    "id", "fabricante", "modelo", "tipo", "potencia_nominal_w", "potencia_max_fv_w",
    "tensao_max_entrada_v", "faixa_mppt_min_v", "faixa_mppt_max_v",
    "corrente_max_entrada_a", "numero_mppt", "compativel_bateria", "preco_brl",
    "fornecedor", "data_coleta", "url_fonte",
)
BATTERY_HEADER = (
    "id", "fabricante", "modelo", "tecnologia", "tensao_nominal_v", "capacidade_ah",
    "capacidade_kwh", "dod_pct", "ciclos", "preco_brl", "fornecedor", "data_coleta",
    "url_fonte",
)


class CatalogValidationError(ValueError):
    """Erro estável com localização no formato arquivo:linha:campo."""

    def __init__(self, filename: str, line: int, field: str, message: str):
        self.filename = filename
        self.line = line
        self.field = field
        self.message = message
        super().__init__(f"{filename}:{line}:{field}: {message}")


def _fail(path: Path, line: int, field: str, message: str):
    raise CatalogValidationError(path.name, line, field, message)


def _text(path: Path, line: int, field: str, value: Optional[str]) -> str:
    result = value.strip() if isinstance(value, str) else ""
    if not result:
        _fail(path, line, field, "campo obrigatório vazio")
    return result


def _decimal(path: Path, line: int, field: str, value: Optional[str]) -> Decimal:
    raw = _text(path, line, field, value)
    try:
        result = Decimal(raw)
    except InvalidOperation:
        _fail(path, line, field, "número decimal inválido")
    if not result.is_finite() or result <= 0:
        _fail(path, line, field, "deve ser um número positivo e finito")
    return result


def _integer(path: Path, line: int, field: str, value: Optional[str]) -> int:
    raw = _text(path, line, field, value)
    try:
        result = int(raw)
    except ValueError:
        _fail(path, line, field, "número inteiro inválido")
    if result <= 0:
        _fail(path, line, field, "deve ser um inteiro positivo")
    return result


def _date(path: Path, line: int, field: str, value: Optional[str]) -> date:
    raw = _text(path, line, field, value)
    try:
        result = date.fromisoformat(raw)
    except ValueError:
        _fail(path, line, field, "data inválida; use YYYY-MM-DD")
    if result > date.today():
        _fail(path, line, field, "data de coleta não pode estar no futuro")
    return result


def _url(path: Path, line: int, field: str, value: Optional[str]) -> str:
    raw = _text(path, line, field, value)
    parsed = urlparse(raw)
    if parsed.scheme != "https" or not parsed.netloc:
        _fail(path, line, field, "URL HTTPS inválida")
    return raw


def _boolean(path: Path, line: int, field: str, value: Optional[str]) -> bool:
    raw = _text(path, line, field, value)
    if raw not in {"true", "false"}:
        _fail(path, line, field, "booleano inválido; use true ou false")
    return raw == "true"


def _rows(path: Path, expected_header: Sequence[str]) -> List[Dict[str, str]]:
    try:
        stream = path.open(encoding="utf-8", newline="")
    except (OSError, UnicodeError) as error:
        _fail(path, 1, "arquivo", f"não foi possível ler: {error}")
    with stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            _fail(path, 1, "cabecalho", "arquivo vazio")
        if tuple(reader.fieldnames) != tuple(expected_header):
            _fail(path, 1, "cabecalho", "cabeçalho diferente do schema esperado")
        rows = list(reader)
    if not rows:
        _fail(path, 2, "registro", "catálogo sem registros")
    for line, row in enumerate(rows, start=2):
        if None in row:
            _fail(path, line, "registro", "quantidade de colunas maior que o cabeçalho")
        for field in expected_header:
            _text(path, line, field, row.get(field))
    return rows


T = TypeVar("T")


def _unique(path: Path, records: Sequence[T], minimum: int):
    seen_ids: Dict[str, int] = {}
    seen_products: Dict[tuple, int] = {}
    for line, record in enumerate(records, start=2):
        record_id = record.id
        product = (record.fabricante.casefold(), record.modelo.casefold())
        if record_id in seen_ids:
            _fail(path, line, "id", f"ID duplicado; primeira ocorrência na linha {seen_ids[record_id]}")
        if product in seen_products:
            _fail(path, line, "modelo", f"produto duplicado; primeira ocorrência na linha {seen_products[product]}")
        seen_ids[record_id] = line
        seen_products[product] = line
    if len(records) < minimum:
        _fail(path, len(records) + 2, "registro", f"mínimo de {minimum} registros; encontrados {len(records)}")


def _common(path: Path, line: int, row: Mapping[str, str]) -> dict:
    return {
        "id": _text(path, line, "id", row.get("id")),
        "fabricante": _text(path, line, "fabricante", row.get("fabricante")),
        "modelo": _text(path, line, "modelo", row.get("modelo")),
        "preco_brl": _decimal(path, line, "preco_brl", row.get("preco_brl")),
        "fornecedor": _text(path, line, "fornecedor", row.get("fornecedor")),
        "data_coleta": _date(path, line, "data_coleta", row.get("data_coleta")),
        "url_fonte": _url(path, line, "url_fonte", row.get("url_fonte")),
    }


def _load_modules(path: Path):
    records = []
    for line, row in enumerate(_rows(path, MODULE_HEADER), start=2):
        values = {field: _decimal(path, line, field, row[field]) for field in (
            "potencia_wp", "voc_v", "isc_a", "vmp_v", "imp_a", "eficiencia_pct"
        )}
        if values["voc_v"] <= values["vmp_v"]:
            _fail(path, line, "voc_v", "deve ser maior que vmp_v")
        if values["isc_a"] <= values["imp_a"]:
            _fail(path, line, "isc_a", "deve ser maior que imp_a")
        if values["eficiencia_pct"] > 100:
            _fail(path, line, "eficiencia_pct", "deve ser menor ou igual a 100")
        records.append(PVModule(**_common(path, line, row), **values))
    _unique(path, records, 10)
    return tuple(records)


def _load_inverters(path: Path):
    records = []
    for line, row in enumerate(_rows(path, INVERTER_HEADER), start=2):
        values = {field: _decimal(path, line, field, row[field]) for field in (
            "potencia_nominal_w", "potencia_max_fv_w", "tensao_max_entrada_v",
            "faixa_mppt_min_v", "faixa_mppt_max_v", "corrente_max_entrada_a"
        )}
        inverter_type = _text(path, line, "tipo", row["tipo"])
        if inverter_type not in {"on-grid", "hibrido"}:
            _fail(path, line, "tipo", "use on-grid ou hibrido")
        battery_compatible = _boolean(path, line, "compativel_bateria", row["compativel_bateria"])
        if battery_compatible != (inverter_type == "hibrido"):
            _fail(path, line, "compativel_bateria", "deve ser true apenas para inversor hibrido")
        if values["potencia_max_fv_w"] < values["potencia_nominal_w"]:
            _fail(path, line, "potencia_max_fv_w", "deve ser maior ou igual à potência nominal")
        if values["faixa_mppt_min_v"] >= values["faixa_mppt_max_v"]:
            _fail(path, line, "faixa_mppt_min_v", "deve ser menor que faixa_mppt_max_v")
        if values["faixa_mppt_max_v"] > values["tensao_max_entrada_v"]:
            _fail(path, line, "faixa_mppt_max_v", "não pode exceder tensao_max_entrada_v")
        records.append(PVInverter(
            **_common(path, line, row), **values, tipo=inverter_type,
            numero_mppt=_integer(path, line, "numero_mppt", row["numero_mppt"]),
            compativel_bateria=battery_compatible,
        ))
    _unique(path, records, 8)
    return tuple(records)


def _load_batteries(path: Path):
    records = []
    for line, row in enumerate(_rows(path, BATTERY_HEADER), start=2):
        values = {field: _decimal(path, line, field, row[field]) for field in (
            "tensao_nominal_v", "capacidade_ah", "capacidade_kwh", "dod_pct"
        )}
        if values["dod_pct"] > 100:
            _fail(path, line, "dod_pct", "deve ser menor ou igual a 100")
        calculated = values["tensao_nominal_v"] * values["capacidade_ah"] / Decimal("1000")
        if abs(values["capacidade_kwh"] - calculated) / calculated > Decimal("0.01"):
            _fail(path, line, "capacidade_kwh", "difere mais de 1% de tensão × Ah")
        records.append(PVBattery(
            **_common(path, line, row), **values,
            tecnologia=_text(path, line, "tecnologia", row["tecnologia"]),
            ciclos=_integer(path, line, "ciclos", row["ciclos"]),
        ))
    _unique(path, records, 6)
    return tuple(records)


def load_pv_catalog(directory: Path = DEFAULT_CATALOG_DIR) -> PVCatalog:
    """Valida os três arquivos antes de devolver qualquer parte do catálogo."""

    directory = Path(directory)
    modules = _load_modules(directory / "modulos.csv")
    inverters = _load_inverters(directory / "inversores.csv")
    batteries = _load_batteries(directory / "baterias.csv")
    return PVCatalog(modules=modules, inverters=inverters, batteries=batteries)


class PVCatalogStore:
    """Publica uma nova fotografia somente após carga integral bem-sucedida."""

    def __init__(self, directory: Path = DEFAULT_CATALOG_DIR):
        self.directory = Path(directory)
        self._catalog: Optional[PVCatalog] = None

    @property
    def catalog(self) -> PVCatalog:
        if self._catalog is None:
            raise RuntimeError("catálogo fotovoltaico ainda não foi carregado")
        return self._catalog

    def reload(self) -> PVCatalog:
        candidate = load_pv_catalog(self.directory)
        self._catalog = candidate
        return candidate
