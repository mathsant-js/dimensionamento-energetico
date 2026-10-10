import shutil
import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker

from app.crud import pv as pv_crud
from app.database import Base
from app.models import PVProposalItem, Property, User
from app.schemas.pv import PVProposalCreate


BACKEND_DIR = Path(__file__).resolve().parents[1]


def proposal_payload(price=Decimal("2500.00")):
    return PVProposalCreate(
        reference_consumption_kwh_month=Decimal("450.000"),
        consumption_calculated_at=datetime(2026, 10, 9, tzinfo=timezone.utc),
        hsp_kwh_m2_day=Decimal("5.100"),
        hsp_source="Entrada manual confirmada pelo usuário",
        hsp_source_date=date(2026, 10, 9),
        target_offset_fraction=Decimal("0.80"),
        performance_ratio=Decimal("0.80"),
        target_energy_kwh=Decimal("360.000"),
        required_pv_power_kwp=Decimal("2.941176"),
        installed_pv_power_kwp=Decimal("3.300000"),
        modules_cost_brl=price,
        inverter_cost_brl=Decimal("4000.00"),
        equipment_cost_brl=price + Decimal("4000.00"),
        total_cost_brl=price + Decimal("4000.00"),
        methodology_version="ADR-001/v1",
        disclaimer="Pré-dimensionamento acadêmico; não substitui projeto executivo.",
        items=[
            {
                "item_type": "module",
                "catalog_id": "MOD-001",
                "manufacturer": "Fabricante teste",
                "model": "M550",
                "description": "Módulo fotovoltaico 550 Wp",
                "quantity": Decimal("5"),
                "unit": "unidade",
                "unit_price_brl": price / 5,
                "subtotal_brl": price,
                "supplier": "Fornecedor brasileiro",
                "source_url": "https://example.test/modulo",
                "collected_at": date(2026, 10, 9),
                "technical_snapshot": {"potencia_wp": 550, "voc_v": 49.9, "vmp_v": 41.8},
                "string_configuration": [{"mppt": 1, "modules": 5}],
            },
            {
                "item_type": "inverter",
                "catalog_id": "INV-001",
                "manufacturer": "Fabricante teste",
                "model": "INV-4K",
                "description": "Inversor 4 kW",
                "quantity": Decimal("1"),
                "unit": "unidade",
                "unit_price_brl": Decimal("4000.00"),
                "subtotal_brl": Decimal("4000.00"),
                "technical_snapshot": {"potencia_max_fv_w": 5000},
                "compatibility_diagnostics": {"compatible": True},
            },
        ],
    )


class ProposalPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tempdir.name) / "test.db"
        self.engine = create_engine(f"sqlite:///{db_path}")

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.user1 = User(name="U1", email="u1@test.local", hashed_password="x", is_active=True)
        self.user2 = User(name="U2", email="u2@test.local", hashed_password="x", is_active=True)
        self.db.add_all([self.user1, self.user2])
        self.db.flush()
        self.property1 = Property(
            user_id=self.user1.id, identification="Casa 1", property_type="house"
        )
        self.property2 = Property(
            user_id=self.user2.id, identification="Casa 2", property_type="house"
        )
        self.db.add_all([self.property1, self.property2])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        self.tempdir.cleanup()

    def test_crud_filters_by_owner_and_keeps_snapshot(self):
        created = pv_crud.create_proposal(
            self.db, self.property1.id, self.user1.id, proposal_payload()
        )
        self.assertIsNotNone(created)
        self.assertEqual(2, len(created.items))
        self.assertEqual(Decimal("2500.00"), created.modules_cost_brl)
        self.assertEqual(550, created.items[0].technical_snapshot["potencia_wp"])

        self.assertIsNone(
            pv_crud.get_proposal(self.db, self.property1.id, created.id, self.user2.id)
        )
        self.assertEqual([], pv_crud.list_proposals(self.db, self.property1.id, self.user2.id))
        self.assertFalse(
            pv_crud.delete_proposal(self.db, self.property1.id, created.id, self.user2.id)
        )
        self.assertIsNotNone(
            pv_crud.get_proposal(self.db, self.property1.id, created.id, self.user1.id)
        )
        self.assertIsNone(
            pv_crud.create_proposal(
                self.db, self.property2.id, self.user1.id, proposal_payload()
            )
        )

    def test_property_deletion_cascades_proposal_and_items(self):
        created = pv_crud.create_proposal(
            self.db, self.property1.id, self.user1.id, proposal_payload()
        )
        proposal_id = created.id
        item_ids = [item.id for item in created.items]
        self.db.delete(self.property1)
        self.db.commit()

        self.assertIsNone(pv_crud.get_proposal(self.db, self.property1.id, proposal_id, self.user1.id))
        self.assertEqual(
            0, self.db.query(PVProposalItem).filter(PVProposalItem.id.in_(item_ids)).count()
        )


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tempdir.cleanup()

    def config_for(self, database_path):
        config = Config(str(BACKEND_DIR / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
        return config

    def test_upgrade_blank_database_and_downgrade_pv_revision(self):
        database_path = Path(self.tempdir.name) / "blank.db"
        config = self.config_for(database_path)
        command.upgrade(config, "head")
        self.assertTrue({"users", "properties", "pv_proposals", "pv_proposal_items"}.issubset(
            set(inspect(create_engine(f"sqlite:///{database_path}")).get_table_names())
        ))

        command.downgrade(config, "20261009_0001")
        tables = set(inspect(create_engine(f"sqlite:///{database_path}")).get_table_names())
        self.assertNotIn("pv_proposals", tables)
        self.assertNotIn("pv_proposal_items", tables)
        self.assertIn("properties", tables)

    def test_upgrade_copy_of_current_database_preserves_existing_data(self):
        source = BACKEND_DIR / "sqlite.db"
        database_path = Path(self.tempdir.name) / "existing.db"
        shutil.copy2(source, database_path)
        with sqlite3.connect(database_path) as connection:
            user_count_before = connection.execute("SELECT count(*) FROM users").fetchone()[0]

        command.upgrade(self.config_for(database_path), "head")
        with sqlite3.connect(database_path) as connection:
            user_count_after = connection.execute("SELECT count(*) FROM users").fetchone()[0]
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
        self.assertEqual(user_count_before, user_count_after)
        self.assertIn("pv_proposals", tables)
        self.assertIn("pv_proposal_items", tables)


if __name__ == "__main__":
    unittest.main()
