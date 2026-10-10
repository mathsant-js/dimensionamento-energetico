"""Add a traceable HSP resource associated with each property.

Revision ID: 20261009_0003
Revises: 20261009_0002
"""
from alembic import op
import sqlalchemy as sa


revision = "20261009_0003"
down_revision = "20261009_0002"
branch_labels = None
depends_on = None


def _table_exists(table_name):
    """Support databases whose tables were previously created by create_all."""
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _ensure_index(index_name, table_name, columns):
    indexes = {
        index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)
    }
    if index_name not in indexes:
        op.create_index(index_name, table_name, columns)


def upgrade():
    if not _table_exists("property_solar_resources"):
        op.create_table(
            "property_solar_resources",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "property_id",
                sa.Integer(),
                sa.ForeignKey("properties.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("hsp_kwh_m2_day", sa.Numeric(8, 3), nullable=False),
            sa.Column("unit", sa.String(30), nullable=False, server_default="kWh/m²/dia"),
            sa.Column("source", sa.Text(), nullable=False),
            sa.Column("source_date", sa.Date(), nullable=False),
            sa.Column("acquisition_mode", sa.String(30), nullable=False, server_default="manual"),
            sa.Column("location_city", sa.String(100)),
            sa.Column("location_state", sa.String(50)),
            sa.Column("location_latitude", sa.Numeric(10, 7)),
            sa.Column("location_longitude", sa.Numeric(10, 7)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("property_id", name="uq_property_solar_resource_property"),
        )
    _ensure_index("ix_property_solar_resources_id", "property_solar_resources", ["id"])
    _ensure_index(
        "ix_property_solar_resources_property_id",
        "property_solar_resources",
        ["property_id"],
    )


def downgrade():
    op.drop_index(
        "ix_property_solar_resources_property_id",
        table_name="property_solar_resources",
    )
    op.drop_index("ix_property_solar_resources_id", table_name="property_solar_resources")
    op.drop_table("property_solar_resources")
