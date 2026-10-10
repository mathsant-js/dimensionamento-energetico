"""Regressão dos dois cenários publicados nas evidências da TASK-34."""

from datetime import date
from decimal import Decimal
import unittest

from app.schemas.pv import PVSimulationRequest
from app.services.pv_catalog import load_pv_catalog
from app.services.pv_simulation import simulate_pv_solution


class Task34DocumentedScenariosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_pv_catalog()
        cls.common = {
            "hsp_kwh_m2_day": "5",
            "hsp_source": "Entrada manual reproduzível da TASK-34",
            "hsp_source_date": date(2026, 10, 10),
            "target_offset_fraction": "1",
            "period_days": 30,
            "performance_ratio": "0.8",
            "module_catalog_id": "MOD-CAN-550-001",
        }

    def simulate(self, **changes):
        request = PVSimulationRequest(**self.common, **changes)
        return simulate_pv_solution(1, Decimal("300"), request, self.catalog)

    def test_documented_on_grid_scenario(self):
        result = self.simulate(inverter_catalog_id="INV-GRO-2500-001")

        self.assertEqual(Decimal("300.000"), result["calculation"]["target_energy"]["value"])
        self.assertEqual(Decimal("2.500000"), result["calculation"]["required_pv_power"]["value"])
        self.assertEqual(5, result["selected_module"]["module_quantity"])
        self.assertEqual(Decimal("2.750000"), result["selected_module"]["installed_power_kwp"])
        self.assertEqual(Decimal("248.000"), result["selected_inverter"]["arrangement"][0]["voc_v"])
        self.assertEqual(Decimal("208.500"), result["selected_inverter"]["arrangement"][0]["vmp_v"])
        self.assertEqual(0, result["storage"]["battery_quantity"])
        self.assertEqual(Decimal("5844.00"), result["budget"]["total_cost_brl"])

    def test_documented_battery_scenario(self):
        result = self.simulate(
            inverter_catalog_id="INV-DEY-5000-001",
            autonomy_hours="12",
            battery_efficiency="0.95",
            battery_catalog_id="BAT-DYN-B4850-001",
            additional_costs=[{"description": "Instalação", "value_brl": "1500.00"}],
        )

        storage = result["storage"]
        self.assertEqual(Decimal("5.000"), storage["autonomy_energy"]["value"])
        self.assertEqual(Decimal("5.848"), storage["required_nominal_capacity"]["value"])
        self.assertEqual(3, storage["battery_quantity"])
        self.assertEqual(Decimal("7.200"), storage["installed_nominal_capacity"]["value"])
        self.assertEqual(Decimal("6.156"), storage["installed_deliverable_energy"]["value"])
        self.assertGreaterEqual(
            storage["installed_deliverable_energy"]["value"],
            storage["autonomy_energy"]["value"],
        )
        self.assertEqual(Decimal("26924.34"), result["budget"]["batteries_cost_brl"])
        self.assertEqual(Decimal("45782.24"), result["budget"]["equipment_cost_brl"])
        self.assertEqual(Decimal("47282.24"), result["budget"]["total_cost_brl"])


if __name__ == "__main__":
    unittest.main()

