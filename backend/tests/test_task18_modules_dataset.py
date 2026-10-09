import csv
import unittest
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse


DATASET = Path(__file__).parents[1] / "data" / "pv" / "modulos.csv"
EXPECTED_HEADER = [
    "id",
    "fabricante",
    "modelo",
    "potencia_wp",
    "voc_v",
    "isc_a",
    "vmp_v",
    "imp_a",
    "eficiencia_pct",
    "preco_brl",
    "fornecedor",
    "data_coleta",
    "url_fonte",
]
NUMERIC_FIELDS = [
    "potencia_wp",
    "voc_v",
    "isc_a",
    "vmp_v",
    "imp_a",
    "eficiencia_pct",
    "preco_brl",
]


class TestTask18ModulesDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with DATASET.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            cls.header = reader.fieldnames
            cls.rows = list(reader)

    def test_exact_header_and_minimum_record_count(self):
        self.assertEqual(EXPECTED_HEADER, self.header)
        self.assertGreaterEqual(len(self.rows), 10)

    def test_required_text_fields_are_not_empty(self):
        for line, row in enumerate(self.rows, start=2):
            for field in EXPECTED_HEADER:
                self.assertTrue(row[field].strip(), f"modulos.csv:{line}:{field}")

    def test_ids_and_products_are_unique(self):
        ids = [row["id"] for row in self.rows]
        products = [(row["fabricante"], row["modelo"]) for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(products), len(set(products)))

    def test_numeric_values_are_positive_and_electrically_coherent(self):
        for line, row in enumerate(self.rows, start=2):
            values = {}
            for field in NUMERIC_FIELDS:
                try:
                    values[field] = Decimal(row[field])
                except InvalidOperation as error:
                    self.fail(f"modulos.csv:{line}:{field}: {error}")
                self.assertGreater(values[field], 0, f"modulos.csv:{line}:{field}")

            self.assertGreater(values["voc_v"], values["vmp_v"])
            self.assertGreater(values["isc_a"], values["imp_a"])
            self.assertLessEqual(values["eficiencia_pct"], 100)

    def test_dates_and_source_urls_are_valid(self):
        for line, row in enumerate(self.rows, start=2):
            collected_on = date.fromisoformat(row["data_coleta"])
            self.assertLessEqual(collected_on, date.today())

            parsed = urlparse(row["url_fonte"])
            self.assertEqual("https", parsed.scheme, f"modulos.csv:{line}:url_fonte")
            self.assertTrue(parsed.netloc, f"modulos.csv:{line}:url_fonte")


if __name__ == "__main__":
    unittest.main()
