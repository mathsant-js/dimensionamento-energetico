"""Regressão unitária consolidada do domínio fotovoltaico da Sprint 2.

As fixtures deste módulo são deliberadamente pequenas, sintéticas e imutáveis.
Elas não consultam a rede nem dependem de preços dos CSVs de produção.
"""

import unittest
from datetime import date
from decimal import Decimal

from app.schemas.pv_catalog import PVBattery, PVInverter, PVModule
from app.services.pv_budget import AdditionalCost, build_pv_bom
from app.services.pv_inverter_selection import select_inverters
from app.services.pv_module_selection import compare_module_options
from app.services.pv_sizing import size_pv_generation
from app.services.storage_sizing import size_battery_storage


COLLECTED_AT = date(2026, 1, 1)


def module(module_id="MOD-TEST", price="500.00"):
    return PVModule(
        id=module_id,
        fabricante="Fabricante de teste",
        modelo=f"Modulo {module_id}",
        potencia_wp=Decimal("500"),
        voc_v=Decimal("50"),
        isc_a=Decimal("14"),
        vmp_v=Decimal("40"),
        imp_a=Decimal("13"),
        eficiencia_pct=Decimal("20"),
        preco_brl=Decimal(price),
        fornecedor="Fornecedor de teste",
        data_coleta=COLLECTED_AT,
        url_fonte="https://example.test/modulo.pdf",
    )


def inverter(inverter_id, *, battery_compatible, price):
    return PVInverter(
        id=inverter_id,
        fabricante="Fabricante de teste",
        modelo=f"Inversor {inverter_id}",
        tipo="hibrido" if battery_compatible else "on-grid",
        potencia_nominal_w=Decimal("5000"),
        potencia_max_fv_w=Decimal("6000"),
        tensao_max_entrada_v=Decimal("500"),
        faixa_mppt_min_v=Decimal("80"),
        faixa_mppt_max_v=Decimal("450"),
        corrente_max_entrada_a=Decimal("20"),
        numero_mppt=2,
        compativel_bateria=battery_compatible,
        preco_brl=Decimal(price),
        fornecedor="Fornecedor de teste",
        data_coleta=COLLECTED_AT,
        url_fonte="https://example.test/inversor.pdf",
    )


def battery():
    return PVBattery(
        id="BAT-TEST",
        fabricante="Fabricante de teste",
        modelo="Bateria 5 kWh",
        tecnologia="LiFePO4",
        tensao_nominal_v=Decimal("50"),
        capacidade_ah=Decimal("100"),
        capacidade_kwh=Decimal("5"),
        dod_pct=Decimal("80"),
        ciclos=6000,
        preco_brl=Decimal("4000.00"),
        fornecedor="Fornecedor de teste",
        data_coleta=COLLECTED_AT,
        url_fonte="https://example.test/bateria.pdf",
    )


class Task32DomainRegressionTests(unittest.TestCase):
    def setUp(self):
        self.module = module()
        self.on_grid = inverter(
            "INV-ON-GRID", battery_compatible=False, price="2000.00"
        )
        self.hybrid = inverter(
            "INV-HYBRID", battery_compatible=True, price="3000.00"
        )

    def sized_module(self):
        sizing = size_pv_generation("450", "0.80", "5", 30, "0.80")
        comparison = compare_module_options(
            sizing.required_pv_power.value,
            (self.module,),
            selected_module_id=self.module.id,
        )
        return sizing, comparison.selected

    def test_on_grid_path_keeps_technical_and_financial_results_consistent(self):
        sizing, module_option = self.sized_module()
        storage = size_battery_storage("450", "0")
        selection = select_inverters(
            module_option,
            self.module,
            (self.hybrid, self.on_grid),
            storage,
        )

        self.assertEqual(Decimal("3.000000"), sizing.required_pv_power.value)
        self.assertEqual(6, module_option.module_quantity)
        self.assertEqual(
            ["INV-ON-GRID", "INV-HYBRID"],
            [item.catalog_id for item in selection.compatible],
        )

        selected = selection.compatible[0]
        budget = build_pv_bom(
            module_option, self.module, selected, self.on_grid, storage
        )

        self.assertEqual(Decimal("3000.00"), budget.modules_cost_brl)
        self.assertEqual(Decimal("2000.00"), budget.inverter_cost_brl)
        self.assertEqual(Decimal("0.00"), budget.batteries_cost_brl)
        self.assertEqual(Decimal("5000.00"), budget.total_cost_brl)
        self.assertEqual(
            budget.total_cost_brl,
            sum((item.subtotal_brl for item in budget.items), Decimal("0.00")),
        )

    def test_storage_path_filters_architecture_and_uses_ceil_in_bom(self):
        _, module_option = self.sized_module()
        selected_battery = battery()
        storage = size_battery_storage(
            "450", "12", selected_battery, battery_efficiency="1"
        )
        selection = select_inverters(
            module_option,
            self.module,
            (self.on_grid, self.hybrid),
            storage,
        )

        self.assertEqual(2, storage.battery_quantity)
        self.assertEqual(["INV-HYBRID"], [item.catalog_id for item in selection.compatible])
        self.assertEqual(["INV-ON-GRID"], [item.catalog_id for item in selection.rejected])
        self.assertEqual(
            "STORAGE_REQUIRES_BATTERY_COMPATIBLE_INVERTER",
            selection.rejected[0].reasons[0].code,
        )

        budget = build_pv_bom(
            module_option,
            self.module,
            selection.compatible[0],
            self.hybrid,
            storage,
            selected_battery,
            (AdditionalCost("Instalação", "1000.00"),),
        )

        self.assertEqual(Decimal("8000.00"), budget.batteries_cost_brl)
        self.assertEqual(Decimal("14000.00"), budget.equipment_cost_brl)
        self.assertEqual(Decimal("15000.00"), budget.total_cost_brl)
        self.assertEqual(
            budget.total_cost_brl,
            sum((item.subtotal_brl for item in budget.items), Decimal("0.00")),
        )


if __name__ == "__main__":
    unittest.main()
