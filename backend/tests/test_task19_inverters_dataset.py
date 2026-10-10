import csv
import unittest
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse


DATASET = Path(__file__).parents[1] / "data" / "pv" / "inversores.csv"
EXPECTED_HEADER = [
    "id",
    "fabricante",
    "modelo",
    "tipo",
    "potencia_nominal_w",
    "potencia_max_fv_w",
    "tensao_max_entrada_v",
    "faixa_mppt_min_v",
    "faixa_mppt_max_v",
    "corrente_max_entrada_a",
    "numero_mppt",
    "compativel_bateria",
    "preco_brl",
    "fornecedor",
    "data_coleta",
    "url_fonte",
]
DECIMAL_FIELDS = [
    "potencia_nominal_w",
    "potencia_max_fv_w",
    "tensao_max_entrada_v",
    "faixa_mppt_min_v",
    "faixa_mppt_max_v",
    "corrente_max_entrada_a",
    "preco_brl",
]
ALLOWED_TYPES = {"on-grid", "hibrido"}
ALLOWED_BOOLEANS = {"true", "false"}


class TestTask19InvertersDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with DATASET.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            cls.header = reader.fieldnames
            cls.rows = list(reader)

    def test_exact_header_and_minimum_record_count(self):
        self.assertEqual(EXPECTED_HEADER, self.header)
        self.assertGreaterEqual(len(self.rows), 8)

    def test_required_fields_are_not_empty(self):
        for line, row in enumerate(self.rows, start=2):
            for field in EXPECTED_HEADER:
                self.assertTrue(row[field].strip(), f"inversores.csv:{line}:{field}")

    def test_ids_and_products_are_unique(self):
        ids = [row["id"] for row in self.rows]
        products = [(row["fabricante"], row["modelo"]) for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(products), len(set(products)))

    def test_values_and_electrical_limits_are_coherent(self):
        for line, row in enumerate(self.rows, start=2):
            values = {}
            for field in DECIMAL_FIELDS:
                try:
                    values[field] = Decimal(row[field])
                except InvalidOperation as error:
                    self.fail(f"inversores.csv:{line}:{field}: {error}")
                self.assertGreater(values[field], 0, f"inversores.csv:{line}:{field}")

            try:
                mppt_count = int(row["numero_mppt"])
            except ValueError as error:
                self.fail(f"inversores.csv:{line}:numero_mppt: {error}")

            self.assertGreater(mppt_count, 0, f"inversores.csv:{line}:numero_mppt")
            self.assertGreaterEqual(values["potencia_max_fv_w"], values["potencia_nominal_w"])
            self.assertLess(values["faixa_mppt_min_v"], values["faixa_mppt_max_v"])
            self.assertLessEqual(values["faixa_mppt_max_v"], values["tensao_max_entrada_v"])

    def test_type_and_battery_boolean_are_normalized(self):
        for line, row in enumerate(self.rows, start=2):
            self.assertIn(row["tipo"], ALLOWED_TYPES, f"inversores.csv:{line}:tipo")
            self.assertIn(
                row["compativel_bateria"],
                ALLOWED_BOOLEANS,
                f"inversores.csv:{line}:compativel_bateria",
            )
            self.assertEqual(row["tipo"] == "hibrido", row["compativel_bateria"] == "true")

    def test_catalog_supports_on_grid_and_battery_scenarios(self):
        self.assertTrue(any(row["tipo"] == "on-grid" for row in self.rows))
        self.assertTrue(any(row["tipo"] == "hibrido" for row in self.rows))
        self.assertTrue(any(row["compativel_bateria"] == "true" for row in self.rows))

    def test_dates_and_source_urls_are_valid(self):
        for line, row in enumerate(self.rows, start=2):
            collected_on = date.fromisoformat(row["data_coleta"])
            self.assertLessEqual(collected_on, date.today())

            parsed = urlparse(row["url_fonte"])
            self.assertEqual("https", parsed.scheme, f"inversores.csv:{line}:url_fonte")
            self.assertTrue(parsed.netloc, f"inversores.csv:{line}:url_fonte")


if __name__ == "__main__":
    unittest.main()
