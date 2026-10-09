"""Register the Sprint 1 schema as an Alembic-compatible baseline.

Revision ID: 20261009_0001
Revises: None
"""
from alembic import op
import sqlalchemy as sa


revision = "20261009_0001"
down_revision = None
branch_labels = None
depends_on = None


def _tables():
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade():
    tables = _tables()
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("hashed_password", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_users_id", "users", ["id"])
        op.create_index("ix_users_name", "users", ["name"])
        op.create_index("ix_users_email", "users", ["email"], unique=True)
    if "properties" not in tables:
        op.create_table(
            "properties",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("identification", sa.String(), nullable=False),
            sa.Column("property_type", sa.String(), nullable=False),
            sa.Column("address", sa.String()), sa.Column("city", sa.String()),
            sa.Column("state", sa.String()), sa.Column("zipcode", sa.String()),
            sa.Column("latitude", sa.Float()), sa.Column("longitude", sa.Float()),
            sa.Column("built_area", sa.Float()), sa.Column("roof_area", sa.Float()),
            sa.Column("orientation", sa.String()), sa.Column("tilt_angle", sa.Float()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        )
        op.create_index("ix_properties_id", "properties", ["id"])
        op.create_index("ix_properties_user_id", "properties", ["user_id"])
    if "equipments" not in tables:
        op.create_table(
            "equipments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("category", sa.String(), nullable=False),
            sa.Column("power_watts", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_equipments_id", "equipments", ["id"])
        op.create_index("ix_equipments_name", "equipments", ["name"])
    if "property_equipments" not in tables:
        op.create_table(
            "property_equipments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
            sa.Column("equipment_id", sa.Integer(), sa.ForeignKey("equipments.id"), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("hours_per_day", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_property_equipments_id", "property_equipments", ["id"])
        op.create_index("ix_property_equipments_property_id", "property_equipments", ["property_id"])
        op.create_index("ix_property_equipments_equipment_id", "property_equipments", ["equipment_id"])


def downgrade():
    # Adoption baseline is deliberately non-destructive for pre-Alembic installations.
    pass
