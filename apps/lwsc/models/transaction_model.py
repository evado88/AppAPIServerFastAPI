from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime
from apps.lwsc.lwscdb import Base
from apps.lwsc.models.attachment_model import Attachment
from apps.lwsc.models.review_stages_model import ReviewStage
from apps.lwsc.models.status_types_model import StatusType
from apps.lwsc.models.transaction_type_model import TransactionType
from apps.lwsc.models.user_model import User
from apps.osawe.models.transaction_group_model import TransactionGroup

# ---------- SQLAlchemy Models ----------
class TransactionDB(Base):
    __tablename__ = "transactions"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String, nullable=True)

    # type of transaction 
    type_id = Column(Integer, ForeignKey("transaction_types.id"), nullable=False)

    # group of transaction
    group_id = Column(Integer, ForeignKey("transaction_groups.id"), nullable=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # customer
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # meter
    meter_id = Column(Integer, ForeignKey("meters.id"), nullable=True)

    # attachment
    attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=True)

    # transaction
    date = Column(DateTime(timezone=True), nullable=False)

    amount = Column(Float, nullable=False)
    comments = Column(String, nullable=True)
    reference = Column(String, nullable=True)

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
    user = relationship("UserDB", back_populates="transactions", lazy="selectin")
    type = relationship(
        "TransactionTypeDB", back_populates="transactions", lazy="selectin"
    )
    group = relationship(
        "TransactionGroupDB", back_populates="transactions", lazy="selectin"
    )
    status = relationship(
        "StatusTypeDB", back_populates="transactions", lazy="selectin"
    )
    stage = relationship(
        "ReviewStageDB", back_populates="transactions", lazy="selectin"
    )
    attachment = relationship(
        "AttachmentDB", back_populates="transaction", lazy="selectin"
    )


# ---------- Pydantic Schemas ----------
class Transaction(BaseModel):
    # id
    id: Optional[int] = None
    code: Optional[str] = None

    # type of transaction i.e. saving, loan, penalty payment, etc
    type_id: int = Field(
        ..., ge=1, description="Type must be greater than or equal to 1"
    )

    # grouo
    group_id: Optional[int] = None

    # user
    user_id: int

    # customer
    customer_id: int
    
    # meter
    meter_id: int

    # attachment
    attachment_id: Optional[int] = None

    # transaction
    date: datetime = Field(..., description="The date for the transaction")

    amount: float = Field(..., description="Transaction amount must be provided")
    comments: Optional[str] = None
    reference: Optional[str] = None

    # approval
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("list_review_stages.id"), nullable=False)

    approval_levels = Column(Integer, nullable=False)

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


        
        
class TransactionWithDetail(Transaction):
    user: User
    type: TransactionType
    group: TransactionGroup
    status: StatusType
    stage: ReviewStage
    attachment: Optional[Attachment] = None


