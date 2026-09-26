from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, Float
from sqlalchemy.orm import relationship
from .user import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    identification = Column(String, nullable=False)  # Nome/Identificação do imóvel
    property_type = Column(String, nullable=False)  # house, apartment, etc.
    address = Column(String, nullable=True)  # For future use
    city = Column(String, nullable=True)  # For future use
    state = Column(String, nullable=True)  # For future use
    zipcode = Column(String, nullable=True)
    latitude = Column(Float)  # For solar calculations
    longitude = Column(Float)  # For solar calculations
    built_area = Column(Float)  # in square meters
    roof_area = Column(Float, nullable=True)  # in square meters for PV (can be null for apartments)
    orientation = Column(String)  # north, south, etc.
    tilt_angle = Column(Float)  # roof tilt in degrees
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="properties")