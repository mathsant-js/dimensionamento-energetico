from sqlalchemy import Column, Integer, String, Float, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Equipment(Base):
    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # Nome do equipamento
    category = Column(String, nullable=False)  # Categoria (ar condicionado, geladeira, etc.)
    power_watts = Column(Float, nullable=False)  # Potência em watts (W)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    property_equipments = relationship("PropertyEquipment", back_populates="equipment", cascade="all, delete-orphan")


class PropertyEquipment(Base):
    __tablename__ = "property_equipments"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)  # Quantidade do equipamento
    hours_per_day = Column(Float, nullable=False, default=1)  # Horas de uso por dia (0-24)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    property = relationship("Property", back_populates="equipments")
    equipment = relationship("Equipment", back_populates="property_equipments")
