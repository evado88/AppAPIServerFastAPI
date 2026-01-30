from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.lwsc.lwscdb import Base
from datetime import datetime

from apps.lwsc.models.attachment_model import Attachment
from apps.lwsc.models.customer_model import Customer, CustomerSimple
from apps.lwsc.models.review_stages_model import ReviewStage
from apps.lwsc.models.town_model import Town
from apps.lwsc.models.walkroute_model import WalkRoute
from apps.lwsc.models.status_types_model import StatusType
from apps.lwsc.models.user_model import User


# ---------- SQLAlchemy Models ----------
class MeterDB(Base):
    __tablename__ = "meters"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # town
    town_id = Column(Integer, ForeignKey("towns.id"), nullable=False)
    
    # customer
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # route
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)

    # attachments
    attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=True)

    # details
    number = Column(String, nullable=False)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # address
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)

    # approval
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)
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
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    user = relationship("UserDB", back_populates="meters", lazy="selectin")
    town = relationship("TownDB", back_populates="meters", lazy="selectin")
    customer = relationship("CustomerDB", back_populates="meters", lazy="selectin")
    meterreadings = relationship(
        "MeterReadingDB", back_populates="meter", lazy="selectin"
    )
    stage = relationship("ReviewStageDB", back_populates="meters", lazy="selectin")
    status = relationship("StatusTypeDB", back_populates="meters", lazy="selectin")
    attachment = relationship("AttachmentDB", back_populates="meter", lazy="selectin")
    route = relationship("WalkRouteDB", back_populates="meters", lazy="selectin")

# ---------- Pydantic Schemas ----------
class MeterSimple(BaseModel):
    # id
    id: Optional[int] = None

    # user
    user_id: int
    
    # town
    town_id: int
    
    # customer
    customer_id: int

    # route
    route_id: int

    # details
    number: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Number must be between 2 and 50 characters",
    )
    name: Optional[str] = None

    # address
    lat: Optional[float] = None
    lon: Optional[float] = None

    class Config:
        orm_mode = True


class Meter(BaseModel):
    # id
    id: Optional[int] = None

    # user
    user_id: int
    
    # town
    town_id: int
    
    # customer
    customer_id: int

    # route
    route_id: int

    # attachments
    attachment_id: Optional[int] = None

    # details
    number: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Number must be between 2 and 50 characters",
    )
    name: Optional[str] = None
    description: Optional[str] = None

    # address
    lat: Optional[float] = None
    lon: Optional[float] = None

    # approval
    status_id: int = Field(
        ..., ge=1, description="Status must be greater than or equal to 1"
    )
    stage_id: int = Field(..., ge=1, le=8, description="Stage must be between 1 and 8")

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

    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]

    class Config:
        orm_mode = True


class MeterWithDetail(Meter):
    user: User
    town: Town
    customer: Customer
    route: WalkRoute
    attachment: Optional[Attachment] = None
    stage: ReviewStage
    status: StatusType

class MeterWithSimpleDetail(MeterSimple):
    customer: CustomerSimple