from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Text,
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from apps.lwsc.lwscdb import Base
from datetime import datetime
from apps.lwsc.models.complaint_department_model import ComplaintDepartment
from apps.lwsc.models.customer_model import Customer
from apps.lwsc.models.review_stages_model import ReviewStageItem
from apps.lwsc.models.status_types_model import StatusTypeItem
from apps.lwsc.models.user_model import User, UserSimple
from sqlalchemy.dialects.postgresql import JSONB
import enum


# ---------- SQLAlchemy Models ----------
class ComplaintDB(Base):
    __tablename__ = "complaints"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # uuid
    uuid = Column(String, unique=True, index=True, nullable=False)

    # customer
    customer_id = Column(Integer, ForeignKey("customers.id"))

    # department
    department_id = Column(Integer, ForeignKey("complaint_departments.id"))

    # complaint
    reference_number = Column(String(50), unique=True, nullable=False)

    category = Column(String, nullable=False)

    priority = Column(String, nullable=False)

    description = Column(Text, nullable=False)

    preferred_contact_method = Column(String, nullable=False)

    is_emergency = Column(Boolean, default=False)

    assigned_to = Column(String(255), nullable=True)

    resolution_notes = Column(Text, nullable=True)

    resolved_at = Column(DateTime, nullable=True)

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
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    stage = relationship("ReviewStageDB", back_populates="complaints", lazy="raise")
    status = relationship("StatusTypeDB", back_populates="complaints", lazy="raise")
    customer = relationship("CustomerDB", back_populates="complaints", lazy="raise")
    department = relationship(
        "ComplaintDepartmentDB", back_populates="complaints", lazy="raise"
    )


# ---------- Pydantic Schemas ----------
class Complaint(BaseModel):
    # id
    id: Optional[int] = None

    uuid: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="The UUID must be between 2 and 50 characters",
    )

    # customer
    customer_id: Optional[int] = None

    # department
    department_id: Optional[int] = None

    # complaint
    reference_number: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Reference number must be between 2 and 50 characters",
    )
    category: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Category must be between 2 and 50 characters",
    )
    priority: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Priority must be between 2 and 50 characters",
    )
    description: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Description must be between 2 and 500 characters",
    )
    preferred_contact_method: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Preferred contact method must be between 2 and 500 characters",
    )
    is_emergency: bool = Field(
        ...,
        description="Is emergecny must be provided",
    )

    assigned_to: Optional[str] = None

    resolution_notes: Optional[str] = None

    resolved_at: Optional[datetime] = None

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
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        orm_mode = True


class ComplaintWithDetail(Complaint):
    customer: Customer
    department: Optional[ComplaintDepartment] = None
    stage: ReviewStageItem
    status: StatusTypeItem
