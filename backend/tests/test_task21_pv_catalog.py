import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from app.services.pv_catalog import CatalogValidationError, PVCatalogStore, load_pv_catalog


SOURCE = Path(__file__).parents[1] / "data" / "pv"


class PVCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        for filename in ("modulos.csv", "inversores.csv", "baterias.csv"):
            shutil.copy2(SOURCE / filename, self.directory / filename)

    def tearDown(self):
        self.temp.cleanup()

    def rows(self, filename):
        path = self.directory / filename
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            return reader.fieldnames, list(reader)

    def write(self, filename, header, rows):
        path = self.directory / filename
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

    def assert_error(self, filename, field, mutate):
        header, rows = self.rows(filename)
        mutate(header, rows)
        self.write(filename, header, rows)
        with self.assertRaises(CatalogValidationError) as context:
            load_pv_catalog(self.directory)
        self.assertRegex(str(context.exception), rf"^{filename}:\d+:{field}:")

    def test_loads_complete_typed_immutable_catalog(self):
        catalog = load_pv_catalog(self.directory)
        self.assertGreaterEqual(len(catalog.modules), 10)
        self.assertGreaterEqual(len(catalog.inverters), 8)
        self.assertGreaterEqual(len(catalog.batteries), 6)
        self.assertIsInstance(catalog.inverters[0].compativel_bateria, bool)
        with self.assertRaises(Exception):
            catalog.modules[0].potencia_wp = 1

    def test_rejects_wrong_header(self):
        self.assert_error("modulos.csv", "cabecalho", lambda header, rows: header.reverse())

    def test_rejects_empty_required_field(self):
        self.assert_error("modulos.csv", "fabricante", lambda header, rows: rows[0].update(fabricante=" "))

    def test_rejects_invalid_type(self):
        self.assert_error("inversores.csv", "numero_mppt", lambda header, rows: rows[0].update(numero_mppt="1.5"))

    def test_rejects_out_of_range_value(self):
        self.assert_error("baterias.csv", "dod_pct", lambda header, rows: rows[0].update(dod_pct="101"))

    def test_rejects_duplicate_id(self):
        self.assert_error("inversores.csv", "id", lambda header, rows: rows[1].update(id=rows[0]["id"]))

    def test_rejects_catalog_below_minimum(self):
        self.assert_error("baterias.csv", "registro", lambda header, rows: rows.pop())

    def test_rejects_file_without_records(self):
        self.assert_error("modulos.csv", "registro", lambda header, rows: rows.clear())

    def test_store_keeps_previous_catalog_when_reload_fails(self):
        store = PVCatalogStore(self.directory)
        original = store.reload()
        header, rows = self.rows("baterias.csv")
        rows[0]["dod_pct"] = "0"
        self.write("baterias.csv", header, rows)
        with self.assertRaises(CatalogValidationError):
            store.reload()
        self.assertIs(store.catalog, original)


if __name__ == "__main__":
    unittest.main()
