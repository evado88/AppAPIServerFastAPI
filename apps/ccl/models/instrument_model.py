from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, List, Optional
from apps.ccl.ccldb import Base
from datetime import datetime

from apps.ccl.models.lab_model import LabItem
from apps.ccl.models.user_model import User
from sqlalchemy.dialects.postgresql import JSONB

# ---------- SQLAlchemy Models ----------
class InstrumentDB(Base):
    __tablename__ = "instruments"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # details
    name = Column(String, nullable=False)
    serial_no = Column(String,  unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    # costs
    cost = Column(Float, nullable=False)
    amortization = Column(Float, nullable=False)
    annual_cost = Column(Float, nullable=False)
    maintenance_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    
    # calibration
    calibration_cycle = Column(Integer, nullable=False)  
    calibration_kit_cost = Column(Float, nullable=False)
    calibration_service_cost = Column(Float, nullable=False)
    calibration_annual_cost = Column(Float, nullable=False)
    
    # lists
    lab_list = Column(JSONB, nullable=False)
    
    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    user = relationship("UserDB", back_populates="instruments", lazy="raise")
    # test_instrument = relationship("TestInstrumentDB", back_populates="instrument", lazy="selectin")

# ---------- Pydantic Schemas ----------
class Instrument(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # details
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name must be between 2 and 50 characters",
    )
    serial_no: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Serial number must be between 2 and 100 characters",
    )
    description: Optional[str] = None
    
    # costs
    cost: float = Field(
        ..., ge=0, description="The cost must be greater or equal to zero"
    )
    amortization: float = Field(
        ..., ge=0, description="The amortization cost must be greater or equal to zero"
    )
    annual_cost: float = Field(
        ..., ge=0, description="The annual cost must be greater or equal to zero"
    )
    maintenance_cost: float = Field(
        ..., ge=0, description="The maintenance cost must be greater or equal to zero"
    )
    total_cost: float = Field(
        ..., ge=0, description="The total cost must be greater or equal to zero"
    )
    # calibration
    calibration_cycle: float = Field(
        ..., ge=0, description="The calibration cycle must be greater or equal to zero"
    )
    calibration_kit_cost: float = Field(
        ..., ge=0, description="The calibration kit cost must be greater or equal to zero"
    )
    calibration_service_cost: float = Field(
        ..., ge=0, description="The calibration service cost must be greater or equal to zero"
    )
    calibration_annual_cost: float = Field(
        ..., ge=0, description="The calibration annual cost must be greater or equal to zero"
    )
    
    # lists
    lab_list: list[dict[str, Any]]= Field(..., description="The lab list must be provided")
    
    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]

    class Config:
        orm_mode = True
        

class InstrumentItem(BaseModel):
    # id
    id: Optional[int] = None
    # user
    user_id: int

    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name must be between 2 and 50 characters",
    )
    class Config:
        orm_mode = True


class InstrumentWithDetail(Instrument):
    user: User
    
class InstrumentParam(BaseModel):
    instrument: Optional[Instrument]=None
    labs: List[LabItem] = []