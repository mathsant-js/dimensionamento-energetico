import unittest
from decimal import Decimal

from app.services.pv_sizing import (
    PVSizingValidationError,
    calculate_required_pv_power,
    calculate_target_energy,
    size_pv_generation,
)


class PVSizingTests(unittest.TestCase):
    def test_known_example_is_reproducible_and_exposes_units(self):
        result = size_pv_generation(
            reference_consumption_kwh_month=Decimal("450"),
            target_offset_fraction=Decimal("0.80"),
            hsp_hours_day=Decimal("5.1"),
            period_days=30,
            performance_ratio=Decimal("0.80"),
        )

        self.assertEqual(Decimal("360.000"), result.target_energy.value)
        self.assertEqual("kWh/mês", result.target_energy.unit)
        self.assertEqual(Decimal("2.941176"), result.required_pv_power.value)
        self.assertEqual("kWp", result.required_pv_power.unit)
        self.assertEqual("kWh/m²/dia", result.hsp.unit)
        self.assertEqual("fração", result.target_offset.unit)
        self.assertEqual("dias", result.period_days.unit)

    def test_individual_pure_functions_have_defined_precision(self):
        energy = calculate_target_energy(Decimal("123.4567"), Decimal("0.3333"))
        power = calculate_required_pv_power(
            energy, Decimal("4.75"), 31, Decimal("0.8125")
        )
        self.assertEqual(Decimal("41.148"), energy)
        self.assertEqual(Decimal("0.343930"), power)

    def test_fraction_boundaries_are_inclusive_only_at_one(self):
        result = size_pv_generation("100", "1", "5", 30, "1")
        self.assertEqual(Decimal("100.000"), result.target_energy.value)
        self.assertEqual(Decimal("0.666667"), result.required_pv_power.value)

        for field, kwargs in (
            ("target_offset_fraction", {"target_offset_fraction": "0"}),
            ("target_offset_fraction", {"target_offset_fraction": "1.0001"}),
            ("performance_ratio", {"performance_ratio": "0"}),
            ("performance_ratio", {"performance_ratio": "1.0001"}),
        ):
            values = dict(
                reference_consumption_kwh_month="100",
                target_offset_fraction="0.8",
                hsp_hours_day="5",
                period_days=30,
                performance_ratio="0.8",
            )
            values.update(kwargs)
            with self.subTest(field=field, value=values[field]):
                with self.assertRaises(PVSizingValidationError) as context:
                    size_pv_generation(**values)
                self.assertEqual(field, context.exception.field)

    def test_zero_and_negative_divisors_are_rejected_before_division(self):
        cases = (
            ("hsp_hours_day", {"hsp_hours_day": "0"}),
            ("hsp_hours_day", {"hsp_hours_day": "-1"}),
            ("period_days", {"period_days": 0}),
            ("period_days", {"period_days": -1}),
        )
        for field, change in cases:
            values = dict(
                reference_consumption_kwh_month="100",
                target_offset_fraction="0.8",
                hsp_hours_day="5",
                period_days=30,
                performance_ratio="0.8",
            )
            values.update(change)
            with self.subTest(field=field, value=values[field]):
                with self.assertRaises(PVSizingValidationError) as context:
                    size_pv_generation(**values)
                self.assertEqual(field, context.exception.field)

    def test_invalid_consumption_and_non_finite_values_are_rejected(self):
        for value in ("0", "-0.1", "NaN", "Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(PVSizingValidationError) as context:
                    size_pv_generation(value, "0.8", "5")
                self.assertEqual("reference_consumption_kwh_month", context.exception.field)

    def test_float_is_rejected_to_avoid_binary_precision_artifacts(self):
        with self.assertRaises(PVSizingValidationError):
            size_pv_generation(450.0, Decimal("0.8"), Decimal("5"))

    def test_result_is_immutable(self):
        result = size_pv_generation("450", "0.8", "5.1")
        with self.assertRaises(Exception):
            result.target_energy = result.reference_consumption


if __name__ == "__main__":
    unittest.main()
