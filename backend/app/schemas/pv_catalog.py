"""Tipos imutáveis usados pelo catálogo fotovoltaico."""

from datetime import date
from decimal import Decimal
from typing import Literal, Tuple

from pydantic import BaseModel, ConfigDict


class CatalogModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    fabricante: str
    modelo: str
    preco_brl: Decimal
    fornecedor: str
    data_coleta: date
    url_fonte: str


class PVModule(CatalogModel):
    potencia_wp: Decimal
    voc_v: Decimal
    isc_a: Decimal
    vmp_v: Decimal
    imp_a: Decimal
    eficiencia_pct: Decimal


class PVInverter(CatalogModel):
    tipo: Literal["on-grid", "hibrido"]
    potencia_nominal_w: Decimal
    potencia_max_fv_w: Decimal
    tensao_max_entrada_v: Decimal
    faixa_mppt_min_v: Decimal
    faixa_mppt_max_v: Decimal
    corrente_max_entrada_a: Decimal
    numero_mppt: int
    compativel_bateria: bool


class PVBattery(CatalogModel):
    tecnologia: str
    tensao_nominal_v: Decimal
    capacidade_ah: Decimal
    capacidade_kwh: Decimal
    dod_pct: Decimal
    ciclos: int


class PVCatalog(BaseModel):
    """Fotografia completa do catálogo; tuplas impedem mutação acidental."""

    model_config = ConfigDict(frozen=True)

    modules: Tuple[PVModule, ...]
    inverters: Tuple[PVInverter, ...]
    batteries: Tuple[PVBattery, ...]
