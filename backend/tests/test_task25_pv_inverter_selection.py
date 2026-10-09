import unittest
from datetime import date
from decimal import Decimal

from app.schemas.pv_catalog import PVInverter, PVModule
from app.services.pv_inverter_selection import (
    PVInverterSelectionError,
    select_inverters,
)
from app.services.pv_module_selection import size_module_option


def module():
    return PVModule(
        id="MOD-1", fabricante="Módulos", modelo="M550",
        potencia_wp=Decimal("550"), voc_v=Decimal("50"), isc_a=Decimal("14"),
        vmp_v=Decimal("40"), imp_a=Decimal("13"), eficiencia_pct=Decimal("22"),
        preco_brl=Decimal("600"), fornecedor="Fornecedor",
        data_coleta=date(2026, 10, 9), url_fonte="https://example.com/module.pdf",
    )


def inverter(inverter_id="INV-1", price="3000", max_power="5000", max_voltage="500",
             mppt_min="80", mppt_max="450", mppts=2):
    return PVInverter(
        id=inverter_id, fabricante="Inversores", modelo=inverter_id, tipo="on-grid",
        potencia_nominal_w=Decimal("3000"), potencia_max_fv_w=Decimal(max_power),
        tensao_max_entrada_v=Decimal(max_voltage), faixa_mppt_min_v=Decimal(mppt_min),
        faixa_mppt_max_v=Decimal(mppt_max), corrente_max_entrada_a=Decimal("20"),
        numero_mppt=mppts, compativel_bateria=False, preco_brl=Decimal(price),
        fornecedor="Fornecedor", data_coleta=date(2026, 10, 9),
        url_fonte="https://example.com/inverter.pdf",
    )


class PVInverterSelectionTests(unittest.TestCase):
    def setUp(self):
        self.module = module()

    def option_for_modules(self, quantity):
        return size_module_option(Decimal(quantity * 550) / Decimal("1000"), self.module)

    def rejection_codes(self, result):
        return {reason.code for reason in result.rejected[0].reasons}

    def test_uses_smallest_valid_balanced_arrangement(self):
        result = select_inverters(
            self.option_for_modules(10), self.module,
            (inverter(max_power="6000", max_voltage="300", mppt_max="250", mppts=3),),
        )

        self.assertEqual(1, len(result.compatible))
        strings = result.compatible[0].arrangement
        self.assertEqual([1, 2], [item.mppt_id for item in strings])
        self.assertEqual([5, 5], [item.module_quantity for item in strings])
        self.assertEqual([Decimal("250.000"), Decimal("250.000")], [item.voc_v for item in strings])
        self.assertEqual([Decimal("200.000"), Decimal("200.000")], [item.vmp_v for item in strings])

    def test_uneven_distribution_is_balanced_and_deterministic(self):
        result = select_inverters(
            self.option_for_modules(11), self.module,
            (inverter(max_power="7000", max_voltage="250", mppt_max="250", mppts=3),),
        )
        self.assertEqual([4, 4, 3], [s.module_quantity for s in result.compatible[0].arrangement])

    def test_rejects_power_above_maximum(self):
        result = select_inverters(self.option_for_modules(6), self.module, (inverter(max_power="3299"),))
        self.assertEqual({"PV_POWER_ABOVE_MAXIMUM"}, self.rejection_codes(result))

    def test_rejects_voc_above_maximum(self):
        result = select_inverters(
            self.option_for_modules(6), self.module,
            (inverter(max_power="4000", max_voltage="149", mppt_min="50", mppt_max="140", mppts=2),),
        )
        self.assertIn("VOC_ABOVE_MAXIMUM", self.rejection_codes(result))

    def test_rejects_vmp_below_lower_mppt_limit(self):
        result = select_inverters(
            self.option_for_modules(4), self.module,
            (inverter(max_power="4000", mppt_min="161", mppt_max="450", mppts=2),),
        )
        self.assertEqual({"VMP_BELOW_MPPT_MINIMUM"}, self.rejection_codes(result))

    def test_rejects_vmp_above_upper_mppt_limit(self):
        result = select_inverters(
            self.option_for_modules(6), self.module,
            (inverter(max_power="4000", max_voltage="500", mppt_min="50", mppt_max="119", mppts=2),),
        )
        self.assertEqual({"VMP_ABOVE_MPPT_MAXIMUM"}, self.rejection_codes(result))

    def test_voltage_limits_are_inclusive(self):
        result = select_inverters(
            self.option_for_modules(6), self.module,
            (inverter("INV-MIN", max_power="4000", max_voltage="150", mppt_min="120", mppt_max="450", mppts=2),
             inverter("INV-MAX", max_power="4000", max_voltage="150", mppt_min="50", mppt_max="120", mppts=2)),
        )
        self.assertEqual(2, len(result.compatible))

    def test_only_compatible_inverters_are_sorted_by_price(self):
        result = select_inverters(
            self.option_for_modules(6), self.module,
            (inverter("INV-B", "3500", max_power="4000"),
             inverter("INV-X", "1000", max_power="3000"),
             inverter("INV-A", "3500", max_power="4000")),
        )
        self.assertEqual(["INV-A", "INV-B"], [item.catalog_id for item in result.compatible])
        self.assertEqual(["INV-X"], [item.catalog_id for item in result.rejected])

    def test_rejects_mismatched_module_and_empty_catalog(self):
        option = self.option_for_modules(6)
        another = module().model_copy(update={"id": "MOD-2"})
        for field, action in (
            ("module", lambda: select_inverters(option, another, (inverter(),))),
            ("inverters", lambda: select_inverters(option, self.module, ())),
        ):
            with self.subTest(field=field):
                with self.assertRaises(PVInverterSelectionError) as context:
                    action()
                self.assertEqual(field, context.exception.field)


if __name__ == "__main__":
    unittest.main()
