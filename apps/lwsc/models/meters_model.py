from sqlalchemy import Column, Float, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, Optional, Any, List
from apps.lwsc.lwscdb import Base
from datetime import date, datetime
from apps.lwsc.models.review_stages_model import ReviewStage
from apps.lwsc.models.status_types_model import StatusType
from apps.lwsc.models.user_model import User, UserSimple


# ---------- SQLAlchemy Models ----------
class MetersDB(Base):
    __tablename__ = "meters"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # properties
    customer_number = Column(String, nullable=False)
    customer_name = Column(String, nullable=True)
    identity_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    communicate_address = Column(String, nullable=True)
    invoice_number = Column(String, nullable=True)
    open_account_date = Column(String, nullable=True)
    station_name = Column(String, nullable=True)
    operator_uid = Column(String, nullable=True)
    province_name = Column(String, nullable=True)
    city_name = Column(String, nullable=True)
    town_name = Column(String, nullable=True)
    village_name = Column(String, nullable=True)
    # approval
    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # status
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)
    # stage
    stage_id = Column(Integer, ForeignKey("list_review_stages.id"), nullable=False)

    approval_levels = Column(Integer, nullable=False)

    review1_at = Column(DateTime(timezone=True), nullable=True)
    review1_by = Column(String, nullable=True)
    review1_comments = Column(String, nullable=True)

    review2_at = Column(DateTime(timezone=True), nullable=True)
    review2_by = Column(String, nullable=True)
    review2_comments = Column(String, nullable=True)

    review3_at = Column(DateTime(timezone=True), nullable=True)
    review3_by = Column(String, nullable=True)
    review3_comments = Column(String, nullable=True)

    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    user = relationship("UserDB", back_populates="meters", lazy="raise")
    status = relationship("StatusTypeDB", back_populates="meters", lazy="raise")
    stage = relationship("ReviewStageDB", back_populates="meters", lazy="raise")

    # links


# ---------- Pydantic Schemas ----------
class Meters(BaseModel):
    # id
    id: Optional[int] = None

    # properties
    customer_number: str = Field(
        ...,
        description="Customer Number must be provided",
    )
    customer_name: Optional[str] = Field(
        ...,
        description="Customer Name must be provided",
    )
    identity_number: Optional[str] = Field(
        ...,
        description="Identity Number must be provided",
    )
    address: Optional[str] = Field(
        ...,
        description="Address must be provided",
    )
    communicate_address: Optional[str] = Field(
        ...,
        description="Communicate Address must be provided",
    )
    invoice_number: Optional[str] = Field(
        ...,
        description="Invoice Number must be provided",
    )
    open_account_date: Optional[str] = Field(
        ...,
        description="Open Account Date must be provided",
    )
    station_name: Optional[str] = Field(
        ...,
        description="Station Name must be provided",
    )
    operator_uid: Optional[str] = Field(
        ...,
        description="Operator UID must be provided",
    )
    province_name: Optional[str] = Field(
        ...,
        description="Province Name must be provided",
    )
    city_name: Optional[str] = Field(
        ...,
        description="City Name must be provided",
    )
    town_name: Optional[str] = Field(
        ...,
        description="Town Name must be provided",
    )
    village_name: Optional[str] = Field(
        ...,
        description="Village Name must be provided",
    )
    # approval
    # user
    user_id: int

    # stage
    stage_id: int = Field(..., ge=1, le=8, description="Stage must be between 1 and 8")

    # status
    status_id: int = Field(
        ..., ge=1, description="Status must be greater than or equal to 1"
    )

    approval_levels: int = Field(
        ..., ge=1, le=3, description="Approval levels must be between 1 and 3"
    )

    review1_at: Optional[datetime] = None
    review1_by: Optional[str] = None
    review1_comments: Optional[str] = None

    review2_at: Optional[datetime] = None
    review2_by: Optional[str] = None
    review2_comments: Optional[str] = None

    review3_at: Optional[datetime] = None
    review3_by: Optional[str] = None
    review3_comments: Optional[str] = None

    # linkage
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        orm_mode = True


class MetersWithDetail(Meters):
    stage: ReviewStage
    status: StatusType
    user: UserSimple


class ParamMetersEdit(BaseModel):
    meters: Optional[MetersWithDetail] = None

    class Config:
        orm_mode = True
