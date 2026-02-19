from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.ccl.ccldb import Base
from datetime import datetime

from apps.ccl.models.instrument_model import Instrument
from apps.ccl.models.test_model import Test
from apps.ccl.models.user_model import User


# ---------- SQLAlchemy Models ----------
class TestInstrumentDB(Base):
    __tablename__ = "test_instrument"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # test
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    
    # instrument
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    
    # annual volumnes
    annual_volume = Column(Integer, nullable=False)
    percent_volume = Column(Float, nullable=False)
    annual_cost = Column(Float, nullable=False)
    
    # service columns
    
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    #user = relationship("UserDB", back_populates="test_instrument", lazy="selectin")
    #test = relationship("TestDB", back_populates="test_instrument", lazy="selectin")
    #instrument = relationship("InstrumentDB", back_populates="test_instrument", lazy="selectin")
# ---------- Pydantic Schemas ----------
class TestInstrument(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # test
    test_id: int
    
    # instrument
    instrument_id: int
    
    # annual volumnes
    annual_volume: int = Field(
        ...,
        ge=0,
        description="Annual volume must be greater or equal to zero",
    )
    percent_volume: float = Field(
        ...,
        ge=0,
        description="Percent volume must be greater or equal to zero",
    )
    annual_cost: float = Field(
        ...,
        ge=0,
        description="Annual cost must be greater or equal to zero",
    )
    
    # instrument usage
    runs_day_week: int = Field(
        ...,
        ge=0,
        description="Runs per day per week must be greater or equal to zero",
    )
    runs_shift_day: int = Field(
        ...,
        ge=0,
        description="Runs per shift per day must be greater or equal to zero",
    )
    runs_annual: int = Field(
        ...,
        ge=0,
        description="Annual runs must be greater or equal to zero",
    )
    runs_average_volume: float = Field(
        ...,
        ge=0,
        description="Average volume per run must be greater or equal to zero",
    )
    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]

    class Config:
        orm_mode = True


class TestInstrumentWithDetail(TestInstrument):
    user: User
    test: Test
    instrument: Instrument
