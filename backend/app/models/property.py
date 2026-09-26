from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, Float
from sqlalchemy.orm import relationship
from .user import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zipcode = Column(String)
    latitude = Column(Float)  # For solar calculations
    longitude = Column(Float)  # For solar calculations
    property_type = Column(String)  # house, apartment, etc.
    built_area = Column(Float)  # in square meters
    roof_area = Column(Float)  # in square meters for PV
    orientation = Column(String)  # north, south, etc.
    tilt_angle = Column(Float)  # roof tilt in degrees
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="properties")