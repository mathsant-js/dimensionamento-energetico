import unittest
from datetime import date
from decimal import Decimal

from app.schemas.pv_catalog import PVModule
from app.services.pv_catalog import load_pv_catalog
from app.services.pv_module_selection import (
    PVModuleSelectionError,
    compare_module_options,
    size_module_option,
)
from app.services.pv_sizing import size_pv_generation


def module(module_id, power_wp, price_brl, manufacturer="Fabricante", model="Modelo"):
    return PVModule(
        id=module_id,
        fabricante=manufacturer,
        modelo=model,
        potencia_wp=Decimal(power_wp),
        voc_v=Decimal("50"),
        isc_a=Decimal("14"),
        vmp_v=Decimal("42"),
        imp_a=Decimal("13"),
        eficiencia_pct=Decimal("22"),
        preco_brl=Decimal(price_brl),
        fornecedor="Fornecedor",
        data_coleta=date(2026, 10, 9),
        url_fonte="https://example.com/modulo.pdf",
    )


class PVModuleSelectionTests(unittest.TestCase):
    def test_formula_rounds_quantity_up_and_calculates_installed_power_and_price(self):
        option = size_module_option(
            Decimal("2.941176"),
            module("MOD-550", "550", "589.00", "Canadian Solar", "CS6W-550MS"),
        )

        self.assertEqual(6, option.module_quantity)
        self.assertEqual(Decimal("3.300000"), option.installed_power_kwp)
        self.assertEqual(Decimal("3534.00"), option.total_price_brl)
        self.assertEqual("Canadian Solar", option.manufacturer)
        self.assertEqual("CS6W-550MS", option.model)
        self.assertEqual(Decimal("550"), option.module_power_wp)

    def test_exact_division_does_not_add_an_extra_module(self):
        option = size_module_option("3.100", module("MOD-620", "620", "821.74"))
        self.assertEqual(5, option.module_quantity)
        self.assertEqual(Decimal("3.100000"), option.installed_power_kwp)
        self.assertEqual(Decimal("4108.70"), option.total_price_brl)

    def test_comparison_uses_sizing_result_and_catalog_without_fixed_values(self):
        sizing = size_pv_generation("450", "0.8", "5.1", 30, "0.8")
        catalog = load_pv_catalog()

        comparison = compare_module_options(
            sizing.required_pv_power.value,
            catalog.modules,
            selected_module_id="MOD-CAN-550-001",
        )

        self.assertEqual(len(catalog.modules), len(comparison.alternatives))
        self.assertEqual("MOD-CAN-550-001", comparison.selected.catalog_id)
        self.assertEqual(6, comparison.selected.module_quantity)
        self.assertEqual(Decimal("3.300000"), comparison.selected.installed_power_kwp)
        self.assertEqual(Decimal("3534.00"), comparison.selected.total_price_brl)
        self.assertEqual(
            sorted(option.total_price_brl for option in comparison.alternatives),
            [option.total_price_brl for option in comparison.alternatives],
        )

    def test_price_ties_have_deterministic_order(self):
        modules = (
            module("MOD-B", "500", "500"),
            module("MOD-A", "500", "500"),
        )
        comparison = compare_module_options("1", modules)
        self.assertEqual(["MOD-A", "MOD-B"], [item.catalog_id for item in comparison.alternatives])
        self.assertIsNone(comparison.selected)

    def test_invalid_power_empty_catalog_and_unknown_selection_are_rejected(self):
        valid_module = module("MOD-1", "550", "600")
        cases = (
            ("required_pv_power_kwp", lambda: compare_module_options("0", (valid_module,))),
            ("required_pv_power_kwp", lambda: compare_module_options("NaN", (valid_module,))),
            ("modules", lambda: compare_module_options("1", ())),
            (
                "selected_module_id",
                lambda: compare_module_options("1", (valid_module,), "inexistente"),
            ),
        )
        for field, action in cases:
            with self.subTest(field=field):
                with self.assertRaises(PVModuleSelectionError) as context:
                    action()
                self.assertEqual(field, context.exception.field)

    def test_results_are_immutable(self):
        comparison = compare_module_options("1", (module("MOD-1", "550", "600"),))
        with self.assertRaises(Exception):
            comparison.alternatives[0].module_quantity = 99


if __name__ == "__main__":
    unittest.main()
