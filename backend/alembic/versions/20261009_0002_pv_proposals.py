"""Add photovoltaic proposal and immutable catalog snapshot tables.

Revision ID: 20261009_0002
Revises: 20261009_0001
"""
from alembic import op
import sqlalchemy as sa


revision = "20261009_0002"
down_revision = "20261009_0001"
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
    if not _table_exists("pv_proposals"):
        op.create_table(
            "pv_proposals",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("reference_consumption_kwh_month", sa.Numeric(14, 3), nullable=False),
            sa.Column("consumption_calculated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("hsp_kwh_m2_day", sa.Numeric(8, 3), nullable=False),
            sa.Column("hsp_unit", sa.String(30), nullable=False, server_default="kWh/m²/dia"),
            sa.Column("hsp_source", sa.Text(), nullable=False),
            sa.Column("hsp_source_date", sa.Date(), nullable=False),
            sa.Column("hsp_is_manual", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("target_offset_fraction", sa.Numeric(6, 5), nullable=False),
            sa.Column("period_days", sa.Integer(), nullable=False, server_default="30"),
            sa.Column("performance_ratio", sa.Numeric(6, 5), nullable=False),
            sa.Column("target_energy_kwh", sa.Numeric(14, 3), nullable=False),
            sa.Column("required_pv_power_kwp", sa.Numeric(14, 6), nullable=False),
            sa.Column("installed_pv_power_kwp", sa.Numeric(14, 6), nullable=False),
            sa.Column("battery_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("autonomy_hours", sa.Numeric(5, 2), nullable=False, server_default="0"),
            sa.Column("battery_efficiency", sa.Numeric(6, 5), nullable=False, server_default="0.95"),
            sa.Column("required_battery_capacity_kwh", sa.Numeric(14, 3), nullable=False, server_default="0"),
            sa.Column("installed_battery_capacity_kwh", sa.Numeric(14, 3), nullable=False, server_default="0"),
            sa.Column("modules_cost_brl", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("inverter_cost_brl", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("batteries_cost_brl", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("additional_cost_brl", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("equipment_cost_brl", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("total_cost_brl", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("methodology_version", sa.String(50), nullable=False),
            sa.Column("disclaimer", sa.Text(), nullable=False),
        )
    _ensure_index("ix_pv_proposals_id", "pv_proposals", ["id"])
    _ensure_index("ix_pv_proposals_property_id", "pv_proposals", ["property_id"])
    _ensure_index("ix_pv_proposals_user_id", "pv_proposals", ["user_id"])

    if not _table_exists("pv_proposal_items"):
        op.create_table(
            "pv_proposal_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("proposal_id", sa.Integer(), sa.ForeignKey("pv_proposals.id", ondelete="CASCADE"), nullable=False),
            sa.Column("item_type", sa.String(20), nullable=False),
            sa.Column("catalog_id", sa.String(100)),
            sa.Column("manufacturer", sa.String(150)),
            sa.Column("model", sa.String(150)),
            sa.Column("description", sa.String(300), nullable=False),
            sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
            sa.Column("unit", sa.String(30), nullable=False),
            sa.Column("unit_price_brl", sa.Numeric(14, 2), nullable=False),
            sa.Column("subtotal_brl", sa.Numeric(14, 2), nullable=False),
            sa.Column("supplier", sa.String(200)),
            sa.Column("source_url", sa.Text()),
            sa.Column("collected_at", sa.Date()),
            sa.Column("technical_snapshot", sa.JSON(), nullable=False),
            sa.Column("string_configuration", sa.JSON()),
            sa.Column("compatibility_diagnostics", sa.JSON()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    _ensure_index("ix_pv_proposal_items_id", "pv_proposal_items", ["id"])
    _ensure_index("ix_pv_proposal_items_proposal_id", "pv_proposal_items", ["proposal_id"])
    _ensure_index("ix_pv_proposal_items_item_type", "pv_proposal_items", ["item_type"])


def downgrade():
    op.drop_index("ix_pv_proposal_items_item_type", table_name="pv_proposal_items")
    op.drop_index("ix_pv_proposal_items_proposal_id", table_name="pv_proposal_items")
    op.drop_index("ix_pv_proposal_items_id", table_name="pv_proposal_items")
    op.drop_table("pv_proposal_items")
    op.drop_index("ix_pv_proposals_user_id", table_name="pv_proposals")
    op.drop_index("ix_pv_proposals_property_id", table_name="pv_proposals")
    op.drop_index("ix_pv_proposals_id", table_name="pv_proposals")
    op.drop_table("pv_proposals")
