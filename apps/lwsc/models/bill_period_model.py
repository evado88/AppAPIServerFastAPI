from sqlalchemy import Boolean, Column, Date, Integer, String, DateTime
from pydantic import BaseModel, Field
from typing import Optional
from apps.lwsc.lwscdb import Base
from datetime import date, datetime


# ---------- SQLAlchemy Models ----------
class BillPeriodDB(Base):
    __tablename__ = "bill_periods"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # period. This is the same period the meter readers work to
    period_date = Column(Date, unique=True, index=True, nullable=False)

    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    description = Column(String, nullable=True)

    # a period is closed until management opens it
    is_open = Column(Boolean, nullable=False, default=False)

    opened_at = Column(DateTime(timezone=True), nullable=True)
    opened_by = Column(String, nullable=True)

    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(String, nullable=True)

    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)


# ---------- Pydantic Schemas ----------
class BillPeriod(BaseModel):
    # id
    id: Optional[int] = None

    # period
    period_date: date = Field(
        ...,
        description="The date for the period must be provided",
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="The name must be between 2 and 50 characters",
    )

    year: int = Field(..., ge=2000, description="The year must be from 2000")
    month: int = Field(..., ge=1, le=12, description="The month must be between 1 and 12")

    description: Optional[str] = None

    # state
    is_open: bool = False

    opened_at: Optional[datetime] = None
    opened_by: Optional[str] = None

    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None

    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        orm_mode = True


class BillPeriodItem(BaseModel):
    # id
    id: Optional[int] = None

    # period
    period_date: date
    name: str
    year: int
    month: int

    # state
    is_open: bool = False

    class Config:
        orm_mode = True


class BillPeriodAction(BaseModel):
    """
    Carries the user opening or closing the period so the change can be traced
    """

    email: Optional[str] = None

    class Config:
        orm_mode = True
