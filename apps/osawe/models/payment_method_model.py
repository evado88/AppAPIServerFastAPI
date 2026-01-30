from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from apps.osawe.osawedb import Base
from apps.osawe.models.attachment_model import Attachment
from apps.osawe.models.member_model import Member
from apps.osawe.models.review_stages_model import ReviewStage
from apps.osawe.models.status_types_model import StatusType
from apps.osawe.models.user_model import User, UserSimple


# ---------- SQLAlchemy Models ----------
class PaymentMethodDB(Base):
    __tablename__ = "payment_methods"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, nullable=False)
    
    # member
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)

    # details
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)

    # mobile
    method_code = Column(String, nullable=True)
    method_number = Column(String, nullable=True)
    method_name = Column(String, nullable=True)

    # banking
    bank_name = Column(String, nullable=True)
    bank_branch_name = Column(String, nullable=True)
    bank_branch_code = Column(String, nullable=True)
    bank_account_name = Column(String, nullable=True)
    bank_account_no = Column(String, nullable=True)

    # approval
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)

    approval_levels = Column(Integer, nullable=False)

    stage_id = Column(Integer, ForeignKey("list_review_stages.id"), nullable=False)

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
    member = relationship("MemberDB", back_populates="paymentmethod", lazy="selectin")
    posting = relationship("MonthlyPostingDB", back_populates="paymentmethod", lazy="selectin")
    stage = relationship("ReviewStageDB", back_populates="paymentmethod", lazy="selectin")
    status = relationship("StatusTypeDB", back_populates="paymentmethod", lazy="selectin")


# ---------- Pydantic Schemas ----------
class PaymentMethod(BaseModel):
    # id
    id: Optional[int] = None

    # member
    user_id: int = Field(
        ..., ge=1, description="Member id must be greater than or equal to 1"
    )
    
    member_id: Optional[int] = None
    
    # banking
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name must be between 3 and 50 characters",
    )
    type: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Type must be between 3 and 50 characters",
    )
    # mobile
    method_code: Optional[str] = None
    method_number: Optional[str] = None
    method_name: Optional[str] = None
    
    # banking
    bank_name: Optional[str] = None
    bank_branch_name: Optional[str] = None
    bank_branch_code: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_no: Optional[str] = None

    # approval
    status_id: int = Field(
        ..., ge=1, le=5, description="Status must be greater than or equal to 1"
    )

    approval_levels: int = Field(
        ..., ge=1, description="Approval levels must be between 1 and 3"
    )

    stage_id: int = Field(..., ge=1, le=8, description="Stage must be between 1 and 8")

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


class PaymentMethodWithDetail(PaymentMethod):
    member: Member
    stage: ReviewStage
    status: StatusType
