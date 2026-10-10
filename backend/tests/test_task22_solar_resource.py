import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker

from app.crud import pv as pv_crud
from app.database import Base
from app.models import Property, User
from app.schemas.pv import PropertySolarResourceUpsert


BACKEND_DIR = Path(__file__).resolve().parents[1]


class SolarResourceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            f"sqlite:///{Path(self.tempdir.name) / 'task22.db'}",
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.user = User(name="User One", email="one@test.local", hashed_password="x", is_active=True)
        self.other_user = User(
            name="User Two", email="two@test.local", hashed_password="x", is_active=True
        )
        self.db.add_all([self.user, self.other_user])
        self.db.flush()
        self.property = Property(
            user_id=self.user.id,
            identification="Casa Solar",
            property_type="house",
            city="São Paulo",
            state="SP",
            latitude=-23.5505,
            longitude=-46.6333,
        )
        self.db.add(self.property)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        self.tempdir.cleanup()

    @staticmethod
    def payload(value=Decimal("5.123")):
        return PropertySolarResourceUpsert(
            hsp_kwh_m2_day=value,
            source="Atlas solar informado pelo usuário",
            source_date=date(2026, 10, 9),
        )

    def test_absent_resource_is_not_invented_and_access_is_isolated(self):
        self.assertIsNone(pv_crud.get_solar_resource(self.db, self.property.id, self.user.id))
        self.assertIsNone(
            pv_crud.upsert_solar_resource(
                self.db, self.property.id, self.other_user.id, self.payload()
            )
        )
        self.assertIsNone(pv_crud.get_solar_resource(self.db, self.property.id, self.other_user.id))

    def test_upsert_persists_provenance_and_location_snapshot(self):
        created = pv_crud.upsert_solar_resource(
            self.db, self.property.id, self.user.id, self.payload()
        )
        self.assertEqual(Decimal("5.123"), created.hsp_kwh_m2_day)
        self.assertEqual("kWh/m²/dia", created.unit)
        self.assertEqual("manual", created.acquisition_mode)
        self.assertEqual("São Paulo", created.location_city)
        self.assertEqual("SP", created.location_state)
        self.assertEqual(Decimal("-23.5505000"), created.location_latitude)

        updated = pv_crud.upsert_solar_resource(
            self.db, self.property.id, self.user.id, self.payload(Decimal("4.900"))
        )
        self.assertEqual(created.id, updated.id)
        self.assertEqual(Decimal("4.900"), updated.hsp_kwh_m2_day)

    def test_api_payload_rejects_zero_negative_and_untrusted_location_mode(self):
        for invalid in (Decimal("0"), Decimal("-1")):
            with self.assertRaises(ValidationError):
                self.payload(invalid)
        with self.assertRaises(ValidationError):
            PropertySolarResourceUpsert(
                hsp_kwh_m2_day=Decimal("5"),
                source="Fonte não configurada",
                source_date=date(2026, 10, 9),
                acquisition_mode="location_source",
            )

class SolarResourceMigrationTests(unittest.TestCase):
    def test_migration_upgrade_and_downgrade(self):
        with tempfile.TemporaryDirectory() as tempdir:
            database_path = Path(tempdir) / "migration.db"
            config = Config(str(BACKEND_DIR / "alembic.ini"))
            config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
            config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

            command.upgrade(config, "head")
            engine = create_engine(f"sqlite:///{database_path}")
            self.assertIn("property_solar_resources", inspect(engine).get_table_names())

            command.downgrade(config, "20261009_0002")
            self.assertNotIn("property_solar_resources", inspect(engine).get_table_names())
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
