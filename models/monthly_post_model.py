from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from database import Base
from helpers import assist
from models.attachment_model import Attachment
from models.configuration_model import SACCOConfiguration
from models.member_model import Member
from models.posting_period_model import PostingPeriod
from models.review_stages_model import ReviewStage
from models.user_model import User, UserSimple
from models.transaction_types_model import TransactionType
from models.transaction_sources_model import TransactionSource
from models.status_types_model import StatusType
from datetime import date, datetime
from sqlalchemy import Sequence


# ---------- SQLAlchemy Models ----------
class MonthlyPostingDB(Base):
    __tablename__ = "monthly_postings"

    # id
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )
    code = Column(String, nullable=True)
    type = Column(Integer, nullable=False)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # member
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)

    # period
    period_id = Column(String, ForeignKey("list_posting_periods.id"), nullable=False)

    # meeting
    missed_meeting_penalty = Column(Float, nullable=False)

    # posting
    date = Column(DateTime(timezone=True), nullable=False)

    saving = Column(Float, nullable=False)
    shares = Column(Float, nullable=False)
    social = Column(Float, nullable=False)
    penalty = Column(Float, nullable=False)

    late_post_penalty = Column(Float, nullable=False)

    loan_interest = Column(Float, nullable=False)
    loan_month_repayment = Column(Float, nullable=False)

    loan_application = Column(Float, nullable=False)

    comments = Column(String, nullable=True)

    # validation
    contribution_total = Column(Float, nullable=False)
    deposit_total = Column(Float, nullable=False)
    receive_total = Column(Float, nullable=False)
    payment_method_type = Column(String, nullable=False)
    payment_method_number = Column(String, nullable=True)
    payment_method_name = Column(String, nullable=True)
    # pop
    pop_attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=True)
    pop_comments = Column(String, nullable=True)

    # approval
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)

    approval_levels = Column(Integer, nullable=False)

    stage_id = Column(Integer, ForeignKey("list_review_stages.id"), nullable=False)

    guarantor_user_email = Column(String, nullable=True)
    guarantor_required = Column(Integer, nullable=True)
    guarantor_at = Column(DateTime(timezone=True), nullable=True)
    guarantor_by = Column(String, nullable=True)
    guarantor_comments = Column(String, nullable=True)

    pop_review_at = Column(DateTime(timezone=True), nullable=True)
    pop_review_by = Column(String, nullable=True)
    pop_review_comments = Column(String, nullable=True)

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
    user = relationship("UserDB", back_populates="postings", lazy="selectin")
    member = relationship("MemberDB", back_populates="postings", lazy="selectin")
    status = relationship("StatusTypeDB", back_populates="postings", lazy="selectin")
    stage = relationship("ReviewStageDB", back_populates="postings", lazy="selectin")
    transactions = relationship("TransactionDB", back_populates="post", lazy="selectin")
    period = relationship("PostingPeriodDB", back_populates="postings", lazy="selectin")
    attachment = relationship("AttachmentDB", back_populates="post", lazy="selectin")


# ---------- Pydantic Schemas ----------
class MonthlyPosting(BaseModel):
    # id
    id: Optional[int] = None
    code: Optional[str] = None
    type: int = Field(..., ge=1, description="The type must be more than or equal to 1")

    # user
    user_id: int = Field(
        ..., ge=1, description="User id must be greater than or equal to 1"
    )

    # member
    member_id:  Optional[int] = None
    
    # period
    period_id: Optional[str] = None

    # meeting
    missed_meeting_penalty: float = Field(
        ..., ge=0, description="Misssed meetimh penalty amount must be greater or equal to zero"
    )
    # posting
    date: datetime = Field(..., description="The date for the monthly posting")

    saving: float = Field(
        ..., gt=0, description="Saving amount must be greater than zero"
    )
    shares: float = Field(
        ..., gt=0, description="Share amount must be greater than zero"
    )
    social: float = Field(
        ..., ge=0, description="Social amount must be greater or equal to zero"
    )
    penalty: float = Field(
        ..., ge=0, description="Penalty amount must be greater or equal to zero"
    )

    late_post_penalty: float = Field(
        ...,
        ge=0,
        description="Late post penalty amount must be greater or equal to zero",
    )

    loan_interest: float = Field(
        ..., ge=0, description="Loan interest amount must be greater or equal to zero"
    )
    loan_month_repayment: float = Field(
        ...,
        ge=0,
        description="Loan monthly repayment amount must be greater or equal to zero",
    )

    loan_application: float = Field(
        ...,
        ge=0,
        description="Loan application amount must be greater or equal to zero",
    )

    comments: Optional[str] = None
    # validation
    contribution_total: float = Field(
        ...,
        ge=0,
        description="Contribution total amount must be greater or equal to zero",
    )
    deposit_total: float = Field(
        ...,
        description="Deposit total amount must be greater or equal to zero",
    )
    receive_total: float = Field(
        ...,
        description="Receive total amount must be greater or equal to zero",
    )
    payment_method_type: str = Field(
        ...,
        description="The payment method is required",
    )
    payment_method_number: Optional[str] = None
    payment_method_name: Optional[str] = None

    # pop
    pop_attachment_id: Optional[int] = None
    pop_comments: Optional[str] = None

    # approval
    status_id: int = Field(
        ..., ge=1, description="Status must be greater than or equal to 1"
    )

    approval_levels: int = Field(
        ..., ge=1, le=3, description="Approval level must be between 1 and 3"
    )

    stage_id: int = Field(..., ge=1, le=8, description="Stage must be between 1 and 8")

    guarantor_user_email: Optional[str] = None
    guarantor_required: Optional[int] = None
    guarantor_at: Optional[datetime] = None
    guarantor_by: Optional[str] = None
    guarantor_comments: Optional[str] = None

    pop_review_at: Optional[datetime] = None
    pop_review_by: Optional[str] = None
    pop_review_comments: Optional[str] = None

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


class MonthlyPostingWithDetail(MonthlyPosting):
    user: UserSimple
    stage: ReviewStage
    status: StatusType
    period: Optional[PostingPeriod] = None
    attachment: Optional[Attachment] = None


class MonthlyPostingWithMemberDetail(MonthlyPosting):
    user: UserSimple
    stage: ReviewStage
    status: StatusType
    period: PostingPeriod
    attachment: Optional[Attachment] = None
    member: Member
