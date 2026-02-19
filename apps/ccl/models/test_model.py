from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Optional
from apps.ccl.ccldb import Base
from datetime import datetime

from apps.ccl.models.lab_model import Lab
from apps.ccl.models.user_model import User
from sqlalchemy.dialects.postgresql import JSONB

# ---------- SQLAlchemy Models ----------
class TestDB(Base):
    __tablename__ = "tests"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # lab
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False)
    
    # details
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # lists
    reagent_list = Column(JSONB, nullable=False)
    instrument_list = Column(JSONB, nullable=False)
    # annual volumnes
    annual_credit = Column(Integer, nullable=False)
    annual_nhima = Column(Integer, nullable=False)
    annual_research = Column(Integer, nullable=False)
    annual_walkins = Column(Integer, nullable=False)
    
    # totals
    annual_shift = Column(Float, nullable=False)
    annual_total = Column(Integer, nullable=False)

    # lab plans
    sites_no = Column(Integer, nullable=False)
    staff_no = Column(Integer, nullable=False)
   
    # instrument usage
    runs_day_week = Column(Integer, nullable=False)
    runs_shift_day = Column(Integer, nullable=False)
    runs_annual = Column(Integer, nullable=False)
    runs_average_volume = Column(Float, nullable=False)
    
    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    user = relationship("UserDB", back_populates="tests", lazy="selectin")
    lab = relationship("LabDB", back_populates="tests", lazy="selectin")
    #test_instrument = relationship("TestInstrumentDB", back_populates="test", lazy="selectin")
    #test_reagent = relationship("TestReagentDB", back_populates="test", lazy="selectin")
# ---------- Pydantic Schemas ----------
class Test(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # lab
    lab_id: int
    
    # details
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name must be between 2 and 50 characters",
    )
    description: Optional[str] = None
    
    # lists
    reagent_list: list[dict[str, Any]]= Field(..., description="The reagent list must be provided")
    instrument_list: list[dict[str, Any]]= Field(..., description="The instrument list must be provided")
    # annual volumnes
    annual_credit: int = Field(
        ...,
        ge=0,
        description="Annual credit must be greater or equal to zero",
    )
    annual_nhima: int = Field(
        ...,
        ge=0,
        description="Annual nhima must be greater or equal to zero",
    )
    annual_research: int = Field(
        ...,
        ge=0,
        description="Annual research must be greater or equal to zero",
    )
    annual_walkins: int = Field(
        ...,
        ge=0,
        description="Annual walkins must be greater or equal to zero",
    )
    
    # totals
    annual_shift: float = Field(
        ...,
        ge=0,
        description="Annual shift must be greater or equal to zero",
    )
    annual_total: int = Field(
        ...,
        ge=0,
        description="Annual total must be greater or equal to zero",
    )

    # lab plans
    sites_no: int = Field(
        ...,
        ge=0,
        description="Sites number must be greater or equal to zero",
    )
    staff_no: int = Field(
        ...,
        ge=0,
        description="Staff number must be greater or equal to zero",
    )
    
    # runs
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
        description="Average volume of runs must be greater or equal to zero",
    )

    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]

    class Config:
        orm_mode = True


class TestWithDetail(Test):
    user: User
    lab: Lab
