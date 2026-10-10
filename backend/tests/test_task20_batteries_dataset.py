import csv
import unittest
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse


DATASET = Path(__file__).parents[1] / "data" / "pv" / "baterias.csv"
EXPECTED_HEADER = [
    "id",
    "fabricante",
    "modelo",
    "tecnologia",
    "tensao_nominal_v",
    "capacidade_ah",
    "capacidade_kwh",
    "dod_pct",
    "ciclos",
    "preco_brl",
    "fornecedor",
    "data_coleta",
    "url_fonte",
]
DECIMAL_FIELDS = [
    "tensao_nominal_v",
    "capacidade_ah",
    "capacidade_kwh",
    "dod_pct",
    "preco_brl",
]
MAX_CAPACITY_RELATIVE_DIFFERENCE = Decimal("0.01")


class TestTask20BatteriesDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with DATASET.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            cls.header = reader.fieldnames
            cls.rows = list(reader)

    def test_exact_header_and_minimum_record_count(self):
        self.assertEqual(EXPECTED_HEADER, self.header)
        self.assertGreaterEqual(len(self.rows), 6)

    def test_required_fields_are_not_empty(self):
        for line, row in enumerate(self.rows, start=2):
            for field in EXPECTED_HEADER:
                self.assertTrue(row[field].strip(), f"baterias.csv:{line}:{field}")

    def test_ids_and_products_are_unique(self):
        ids = [row["id"] for row in self.rows]
        products = [(row["fabricante"], row["modelo"]) for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(products), len(set(products)))

    def test_numeric_values_and_ranges_are_valid(self):
        for line, row in enumerate(self.rows, start=2):
            values = {}
            for field in DECIMAL_FIELDS:
                try:
                    values[field] = Decimal(row[field])
                except InvalidOperation as error:
                    self.fail(f"baterias.csv:{line}:{field}: {error}")
                self.assertGreater(values[field], 0, f"baterias.csv:{line}:{field}")

            try:
                cycles = int(row["ciclos"])
            except ValueError as error:
                self.fail(f"baterias.csv:{line}:ciclos: {error}")

            self.assertGreater(cycles, 0, f"baterias.csv:{line}:ciclos")
            self.assertLessEqual(values["dod_pct"], 100, f"baterias.csv:{line}:dod_pct")

    def test_declared_capacity_matches_voltage_times_amp_hours(self):
        for line, row in enumerate(self.rows, start=2):
            voltage = Decimal(row["tensao_nominal_v"])
            amp_hours = Decimal(row["capacidade_ah"])
            declared_kwh = Decimal(row["capacidade_kwh"])
            calculated_kwh = voltage * amp_hours / Decimal("1000")
            relative_difference = abs(declared_kwh - calculated_kwh) / calculated_kwh

            self.assertLessEqual(
                relative_difference,
                MAX_CAPACITY_RELATIVE_DIFFERENCE,
                f"baterias.csv:{line}:capacidade_kwh",
            )

    def test_dates_and_source_urls_are_valid(self):
        for line, row in enumerate(self.rows, start=2):
            collected_on = date.fromisoformat(row["data_coleta"])
            self.assertLessEqual(collected_on, date.today())

            parsed = urlparse(row["url_fonte"])
            self.assertEqual("https", parsed.scheme, f"baterias.csv:{line}:url_fonte")
            self.assertTrue(parsed.netloc, f"baterias.csv:{line}:url_fonte")


if __name__ == "__main__":
    unittest.main()
