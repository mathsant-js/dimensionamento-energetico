from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from ..database import Base


class PropertySolarResource(Base):
    """HSP confirmed for a property, with its source and location provenance."""

    __tablename__ = "property_solar_resources"
    __table_args__ = (UniqueConstraint("property_id", name="uq_property_solar_resource_property"),)

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hsp_kwh_m2_day = Column(Numeric(8, 3), nullable=False)
    unit = Column(String(30), nullable=False, default="kWh/m²/dia")
    source = Column(Text, nullable=False)
    source_date = Column(Date, nullable=False)
    acquisition_mode = Column(String(30), nullable=False, default="manual")
    location_city = Column(String(100), nullable=True)
    location_state = Column(String(50), nullable=True)
    location_latitude = Column(Numeric(10, 7), nullable=True)
    location_longitude = Column(Numeric(10, 7), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    property = relationship("Property", back_populates="solar_resource")


class PVProposal(Base):
    """Persisted, reproducible snapshot of one photovoltaic proposal."""

    __tablename__ = "pv_proposals"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status = Column(String(30), nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    reference_consumption_kwh_month = Column(Numeric(14, 3), nullable=False)
    consumption_calculated_at = Column(DateTime(timezone=True), nullable=False)
    hsp_kwh_m2_day = Column(Numeric(8, 3), nullable=False)
    hsp_unit = Column(String(30), nullable=False, default="kWh/m²/dia")
    hsp_source = Column(Text, nullable=False)
    hsp_source_date = Column(Date, nullable=False)
    hsp_is_manual = Column(Boolean, nullable=False, default=True)
    target_offset_fraction = Column(Numeric(6, 5), nullable=False)
    period_days = Column(Integer, nullable=False, default=30)
    performance_ratio = Column(Numeric(6, 5), nullable=False)
    target_energy_kwh = Column(Numeric(14, 3), nullable=False)
    required_pv_power_kwp = Column(Numeric(14, 6), nullable=False)
    installed_pv_power_kwp = Column(Numeric(14, 6), nullable=False)

    battery_requested = Column(Boolean, nullable=False, default=False)
    autonomy_hours = Column(Numeric(5, 2), nullable=False, default=0)
    battery_efficiency = Column(Numeric(6, 5), nullable=False, default=0.95)
    required_battery_capacity_kwh = Column(Numeric(14, 3), nullable=False, default=0)
    installed_battery_capacity_kwh = Column(Numeric(14, 3), nullable=False, default=0)

    modules_cost_brl = Column(Numeric(14, 2), nullable=False, default=0)
    inverter_cost_brl = Column(Numeric(14, 2), nullable=False, default=0)
    batteries_cost_brl = Column(Numeric(14, 2), nullable=False, default=0)
    additional_cost_brl = Column(Numeric(14, 2), nullable=False, default=0)
    equipment_cost_brl = Column(Numeric(14, 2), nullable=False, default=0)
    total_cost_brl = Column(Numeric(14, 2), nullable=False, default=0)
    methodology_version = Column(String(50), nullable=False)
    disclaimer = Column(Text, nullable=False)

    property = relationship("Property", back_populates="pv_proposals")
    user = relationship("User", back_populates="pv_proposals")
    items = relationship(
        "PVProposalItem",
        back_populates="proposal",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PVProposalItem.id",
    )


class PVProposalItem(Base):
    """Commercial and technical snapshot detached from mutable CSV catalogs."""

    __tablename__ = "pv_proposal_items"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(
        Integer, ForeignKey("pv_proposals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_type = Column(String(20), nullable=False, index=True)
    catalog_id = Column(String(100), nullable=True)
    manufacturer = Column(String(150), nullable=True)
    model = Column(String(150), nullable=True)
    description = Column(String(300), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit = Column(String(30), nullable=False)
    unit_price_brl = Column(Numeric(14, 2), nullable=False)
    subtotal_brl = Column(Numeric(14, 2), nullable=False)
    supplier = Column(String(200), nullable=True)
    source_url = Column(Text, nullable=True)
    collected_at = Column(Date, nullable=True)
    technical_snapshot = Column(JSON, nullable=False, default=dict)
    string_configuration = Column(JSON, nullable=True)
    compatibility_diagnostics = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    proposal = relationship("PVProposal", back_populates="items")
