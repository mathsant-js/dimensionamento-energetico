import unittest
from datetime import date
from decimal import Decimal

from app.schemas.pv_catalog import PVBattery
from app.services.pv_catalog import load_pv_catalog
from app.services.storage_sizing import (
    StorageSizingValidationError,
    size_battery_storage,
)


def battery(capacity="5", dod_pct="80", price="6000"):
    return PVBattery(
        id="BAT-1",
        fabricante="Baterias",
        modelo="B5",
        tecnologia="LiFePO4",
        tensao_nominal_v=Decimal("50"),
        capacidade_ah=Decimal("100"),
        capacidade_kwh=Decimal(capacity),
        dod_pct=Decimal(dod_pct),
        ciclos=6000,
        preco_brl=Decimal(price),
        fornecedor="Fornecedor",
        data_coleta=date(2026, 10, 9),
        url_fonte="https://example.com/battery.pdf",
    )


class StorageSizingTests(unittest.TestCase):
    def test_zero_autonomy_needs_no_battery_and_has_zero_capacity_and_cost(self):
        result = size_battery_storage("300", "0")

        self.assertFalse(result.storage_requested)
        self.assertEqual(Decimal("10.000"), result.daily_consumption.value)
        self.assertEqual("kWh/mês", result.reference_consumption.unit)
        self.assertEqual("kWh/dia", result.daily_consumption.unit)
        self.assertEqual(Decimal("0.000"), result.autonomy_energy.value)
        self.assertEqual(0, result.battery_quantity)
        self.assertEqual(Decimal("0.000"), result.required_nominal_capacity.value)
        self.assertEqual(Decimal("0.000"), result.installed_nominal_capacity.value)
        self.assertEqual(Decimal("0.00"), result.total_battery_cost.value)
        self.assertIsNone(result.battery_catalog_id)

    def test_active_storage_uses_nominal_capacity_without_applying_dod_twice(self):
        result = size_battery_storage(
            "300", "24", battery(), battery_efficiency="1"
        )

        self.assertTrue(result.storage_requested)
        self.assertEqual(Decimal("10.000"), result.autonomy_energy.value)
        self.assertEqual(Decimal("12.500"), result.required_nominal_capacity.value)
        self.assertEqual(3, result.battery_quantity)
        self.assertEqual(Decimal("15.000"), result.installed_nominal_capacity.value)
        self.assertEqual(Decimal("12.000"), result.installed_deliverable_energy.value)
        self.assertEqual(Decimal("18000.00"), result.total_battery_cost.value)

    def test_quantity_rounds_up_using_unrounded_required_capacity(self):
        result = size_battery_storage(
            "108.0000108", "24", battery(capacity="4", dod_pct="90"),
            battery_efficiency="1",
        )

        self.assertEqual(2, result.battery_quantity)
        self.assertGreaterEqual(
            result.installed_deliverable_energy.value, result.autonomy_energy.value
        )

    def test_valid_autonomy_and_fraction_limits_are_inclusive(self):
        result = size_battery_storage(
            "120", "24", battery(capacity="4", dod_pct="100"),
            period_days=30, battery_efficiency="1",
        )
        self.assertEqual(1, result.battery_quantity)
        self.assertEqual(Decimal("4.000"), result.autonomy_energy.value)
        self.assertEqual(Decimal("4.000"), result.installed_deliverable_energy.value)

    def test_real_catalog_battery_can_be_sized(self):
        selected = load_pv_catalog().batteries[0]
        result = size_battery_storage("450", "8", selected)

        self.assertEqual(selected.id, result.battery_catalog_id)
        self.assertGreater(result.battery_quantity, 0)
        self.assertGreaterEqual(
            result.installed_deliverable_energy.value, result.autonomy_energy.value
        )

    def test_invalid_inputs_have_stable_fields(self):
        cases = (
            ("reference_consumption_kwh_month", lambda: size_battery_storage("0", "0")),
            ("autonomy_hours", lambda: size_battery_storage("100", "-0.1")),
            ("autonomy_hours", lambda: size_battery_storage("100", "24.1")),
            ("period_days", lambda: size_battery_storage("100", "0", period_days=0)),
            ("battery_efficiency", lambda: size_battery_storage("100", "1", battery(), battery_efficiency="0")),
            ("battery_efficiency", lambda: size_battery_storage("100", "1", battery(), battery_efficiency="1.01")),
            ("battery", lambda: size_battery_storage("100", "1")),
            ("battery.dod_pct", lambda: size_battery_storage("100", "1", battery(dod_pct="0"))),
            ("battery.dod_pct", lambda: size_battery_storage("100", "1", battery(dod_pct="101"))),
        )
        for field, action in cases:
            with self.subTest(field=field):
                with self.assertRaises(StorageSizingValidationError) as context:
                    action()
                self.assertEqual(field, context.exception.field)

    def test_float_and_non_finite_values_are_rejected(self):
        for value in (1.0, "NaN", "Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(StorageSizingValidationError):
                    size_battery_storage("100", value, battery())

    def test_result_is_immutable(self):
        result = size_battery_storage("100", "0")
        with self.assertRaises(Exception):
            result.battery_quantity = 1


if __name__ == "__main__":
    unittest.main()
