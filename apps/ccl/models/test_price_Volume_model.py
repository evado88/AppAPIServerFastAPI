from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Optional
from apps.ccl.ccldb import Base
from datetime import datetime

from apps.ccl.models.month_model import Month
from apps.ccl.models.user_model import User, UserSimple


# ---------- SQLAlchemy Models ----------
class TestPriceVolmeDB(Base):
    __tablename__ = "test_price_volumes"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # details
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # period
    month_id = Column(Integer,  ForeignKey("list_months.id"), nullable=False)
    year = Column(Integer, nullable=False)
    
    #price volumnes
    price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

    
    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    user = relationship("UserDB", back_populates="testpricevolumes", lazy="raise")
    month = relationship("MonthDB", back_populates="testpricevolumes", lazy="raise")
   
# ---------- Pydantic Schemas ----------
class TestPriceVolme(BaseModel):
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
    description: Optional[str] = None
    
    # period
    month_id: int = Field(
        ...,
        ge=1,
        le=12,
        description="Month must be between 1 and 12",
    )
    year: int = Field(
        ...,
        ge=2020,
        le=2036,
        description="Years must be between 2020 and 2036",
    )
    
    #price volumnes
    volume: int = Field(
        ...,
        ge=0,
        description="Volume must be greater or equal to zero",
    )
    price: float = Field(
        ...,
        ge=0,
        description="Price must be greater or equal to zero",
    )
    
    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]

    class Config:
        orm_mode = True

        
class TestPriceVolmeWithDetail(TestPriceVolme):
    user: UserSimple
    month: Month