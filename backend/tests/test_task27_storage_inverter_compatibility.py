import unittest
from datetime import date
from decimal import Decimal

from app.schemas.pv_catalog import PVBattery, PVInverter, PVModule
from app.services.pv_inverter_selection import (
    PVInverterSelectionError,
    require_budget_eligible_inverter,
    select_inverters,
)
from app.services.pv_module_selection import size_module_option
from app.services.storage_sizing import size_battery_storage


def module():
    return PVModule(
        id="MOD-1", fabricante="Módulos", modelo="M550",
        potencia_wp=Decimal("550"), voc_v=Decimal("50"), isc_a=Decimal("14"),
        vmp_v=Decimal("40"), imp_a=Decimal("13"), eficiencia_pct=Decimal("22"),
        preco_brl=Decimal("600"), fornecedor="Fornecedor",
        data_coleta=date(2026, 10, 9), url_fonte="https://example.com/module.pdf",
    )


def inverter(inverter_id, battery_compatible, price):
    return PVInverter(
        id=inverter_id, fabricante="Inversores", modelo=inverter_id,
        tipo="hibrido" if battery_compatible else "on-grid",
        potencia_nominal_w=Decimal("5000"), potencia_max_fv_w=Decimal("6000"),
        tensao_max_entrada_v=Decimal("500"), faixa_mppt_min_v=Decimal("80"),
        faixa_mppt_max_v=Decimal("450"), corrente_max_entrada_a=Decimal("20"),
        numero_mppt=2, compativel_bateria=battery_compatible,
        preco_brl=Decimal(price), fornecedor="Fornecedor",
        data_coleta=date(2026, 10, 9), url_fonte="https://example.com/inverter.pdf",
    )


def battery():
    return PVBattery(
        id="BAT-1", fabricante="Baterias", modelo="B5", tecnologia="LiFePO4",
        tensao_nominal_v=Decimal("50"), capacidade_ah=Decimal("100"),
        capacidade_kwh=Decimal("5"), dod_pct=Decimal("80"), ciclos=6000,
        preco_brl=Decimal("6000"), fornecedor="Fornecedor",
        data_coleta=date(2026, 10, 9), url_fonte="https://example.com/battery.pdf",
    )


class StorageInverterCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.module = module()
        self.option = size_module_option("3.3", self.module)
        self.on_grid = inverter("INV-ON-GRID", False, "2000")
        self.hybrid = inverter("INV-HYBRID", True, "4000")

    def test_without_storage_keeps_on_grid_and_hybrid_inverters(self):
        storage = size_battery_storage("300", "0")
        result = select_inverters(
            self.option, self.module, (self.hybrid, self.on_grid), storage
        )

        self.assertEqual(
            ["INV-ON-GRID", "INV-HYBRID"],
            [item.catalog_id for item in result.compatible],
        )
        self.assertEqual((), result.rejected)

    def test_active_storage_rejects_on_grid_with_visible_reason(self):
        storage = size_battery_storage("300", "8", battery())
        result = select_inverters(
            self.option, self.module, (self.on_grid, self.hybrid), storage
        )

        self.assertEqual(["INV-HYBRID"], [item.catalog_id for item in result.compatible])
        self.assertEqual(["INV-ON-GRID"], [item.catalog_id for item in result.rejected])
        reason = result.rejected[0].reasons[0]
        self.assertEqual(
            "STORAGE_REQUIRES_BATTERY_COMPATIBLE_INVERTER", reason.code
        )
        self.assertIn("armazenamento ativo", reason.message)

    def test_incompatible_inverter_cannot_advance_to_budget(self):
        storage = size_battery_storage("300", "8", battery())
        result = select_inverters(
            self.option, self.module, (self.on_grid, self.hybrid), storage
        )

        with self.assertRaises(PVInverterSelectionError) as context:
            require_budget_eligible_inverter(result, "INV-ON-GRID")

        self.assertEqual("inverter_catalog_id", context.exception.field)
        self.assertIn(
            "STORAGE_REQUIRES_BATTERY_COMPATIBLE_INVERTER",
            context.exception.message,
        )
        selected = require_budget_eligible_inverter(result, "INV-HYBRID")
        self.assertEqual("INV-HYBRID", selected.catalog_id)

    def test_invalid_storage_result_is_rejected(self):
        with self.assertRaises(PVInverterSelectionError) as context:
            select_inverters(
                self.option, self.module, (self.on_grid,), storage=True
            )
        self.assertEqual("storage", context.exception.field)


if __name__ == "__main__":
    unittest.main()
