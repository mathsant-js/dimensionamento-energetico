import unittest
from datetime import date
from decimal import Decimal

from app.schemas.pv_catalog import PVBattery, PVInverter, PVModule
from app.services.pv_budget import (
    AdditionalCost,
    PVBudgetValidationError,
    build_pv_bom,
)
from app.services.pv_inverter_selection import select_inverters
from app.services.pv_module_selection import size_module_option
from app.services.storage_sizing import size_battery_storage


def module():
    return PVModule(
        id="MOD-1", fabricante="Solar", modelo="M550", potencia_wp=Decimal("550"),
        voc_v=Decimal("50"), isc_a=Decimal("14"), vmp_v=Decimal("40"),
        imp_a=Decimal("13"), eficiencia_pct=Decimal("22"),
        preco_brl=Decimal("589.005"), fornecedor="Fornecedor BR",
        data_coleta=date(2026, 10, 9), url_fonte="https://example.com/module.pdf",
    )


def inverter(battery_compatible=True):
    return PVInverter(
        id="INV-1", fabricante="Inversores", modelo="I5K",
        tipo="hibrido" if battery_compatible else "on-grid",
        potencia_nominal_w=Decimal("5000"), potencia_max_fv_w=Decimal("6000"),
        tensao_max_entrada_v=Decimal("500"), faixa_mppt_min_v=Decimal("80"),
        faixa_mppt_max_v=Decimal("450"), corrente_max_entrada_a=Decimal("20"),
        numero_mppt=2, compativel_bateria=battery_compatible,
        preco_brl=Decimal("2500.004"), fornecedor="Fornecedor BR",
        data_coleta=date(2026, 10, 9), url_fonte="https://example.com/inverter.pdf",
    )


def battery():
    return PVBattery(
        id="BAT-1", fabricante="Baterias", modelo="B5", tecnologia="LiFePO4",
        tensao_nominal_v=Decimal("50"), capacidade_ah=Decimal("100"),
        capacidade_kwh=Decimal("5"), dod_pct=Decimal("80"), ciclos=6000,
        preco_brl=Decimal("6000.005"), fornecedor="Fornecedor BR",
        data_coleta=date(2026, 10, 9), url_fonte="https://example.com/battery.pdf",
    )


def solution(autonomy="0", battery_compatible=True):
    selected_module = module()
    option = size_module_option("3.3", selected_module)
    selected_battery = battery() if Decimal(autonomy) > 0 else None
    storage = size_battery_storage("300", autonomy, selected_battery)
    selected_inverter = inverter(battery_compatible)
    selection = select_inverters(option, selected_module, (selected_inverter,), storage)
    compatible = selection.compatible[0] if selection.compatible else None
    return selected_module, option, selected_inverter, compatible, selected_battery, storage


class PVBudgetTests(unittest.TestCase):
    def test_without_battery_has_zero_battery_cost_and_server_calculated_totals(self):
        selected_module, option, selected_inverter, compatible, _, storage = solution()
        budget = build_pv_bom(
            option, selected_module, compatible, selected_inverter, storage
        )

        self.assertEqual(["module", "inverter"], [item.category for item in budget.items])
        self.assertEqual(Decimal("3534.06"), budget.modules_cost_brl)
        self.assertEqual(Decimal("2500.00"), budget.inverter_cost_brl)
        self.assertEqual(Decimal("0.00"), budget.batteries_cost_brl)
        self.assertEqual(Decimal("6034.06"), budget.equipment_cost_brl)
        self.assertEqual(budget.equipment_cost_brl, budget.total_cost_brl)

    def test_with_battery_adds_units_and_equipment_cost(self):
        selected_module, option, selected_inverter, compatible, selected_battery, storage = solution("8")
        budget = build_pv_bom(
            option, selected_module, compatible, selected_inverter, storage, selected_battery
        )

        battery_item = next(item for item in budget.items if item.category == "battery")
        self.assertEqual(storage.battery_quantity, battery_item.quantity)
        self.assertEqual(Decimal("6000.01"), battery_item.unit_price_brl)
        self.assertEqual(Decimal("6000.01"), budget.batteries_cost_brl)
        self.assertEqual(Decimal("12034.07"), budget.equipment_cost_brl)

    def test_explicit_additional_costs_are_rounded_and_summed_without_percentage(self):
        selected_module, option, selected_inverter, compatible, _, storage = solution()
        budget = build_pv_bom(
            option, selected_module, compatible, selected_inverter, storage,
            additional_costs=(
                AdditionalCost("Instalação", Decimal("1000.005")),
                AdditionalCost("Frete", Decimal("250.004")),
            ),
        )

        self.assertEqual(Decimal("1250.01"), budget.additional_cost_brl)
        self.assertEqual(Decimal("7284.07"), budget.total_cost_brl)
        self.assertEqual(2, len([item for item in budget.items if item.category == "additional"]))

    def test_rejects_invalid_additional_cost_and_inconsistent_components(self):
        selected_module, option, selected_inverter, compatible, _, storage = solution()
        cases = (
            ("additional_costs[0].description", lambda: build_pv_bom(
                option, selected_module, compatible, selected_inverter, storage,
                additional_costs=(AdditionalCost("  ", "10"),),
            )),
            ("additional_costs[0].value_brl", lambda: build_pv_bom(
                option, selected_module, compatible, selected_inverter, storage,
                additional_costs=(AdditionalCost("Frete", "-0.01"),),
            )),
            ("module", lambda: build_pv_bom(
                option, selected_module.model_copy(update={"id": "OUTRO"}),
                compatible, selected_inverter, storage,
            )),
        )
        for field, action in cases:
            with self.subTest(field=field):
                with self.assertRaises(PVBudgetValidationError) as context:
                    action()
                self.assertEqual(field, context.exception.field)

    def test_storage_cannot_be_budgeted_with_incompatible_or_missing_battery(self):
        selected_module, option, selected_inverter, compatible, _, storage = solution()
        with self.assertRaises(PVBudgetValidationError) as context:
            build_pv_bom(
                option, selected_module, compatible, selected_inverter, storage, battery()
            )
        self.assertEqual("battery", context.exception.field)

        selected_module, option, selected_inverter, compatible, _, storage = solution(
            "8", battery_compatible=False
        )
        self.assertIsNone(compatible)

    def test_budget_and_items_are_immutable(self):
        selected_module, option, selected_inverter, compatible, _, storage = solution()
        budget = build_pv_bom(
            option, selected_module, compatible, selected_inverter, storage
        )
        with self.assertRaises(Exception):
            budget.total_cost_brl = Decimal("0")
        with self.assertRaises(Exception):
            budget.items[0].quantity = 99


if __name__ == "__main__":
    unittest.main()
