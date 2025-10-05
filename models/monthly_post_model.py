from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional
from database import Base
from models.review_stages_model import ReviewStage
from models.user_model import User
from models.transaction_types_model import TransactionType
from models.transaction_sources_model import TransactionSource
from models.status_types_model import StatusType
from datetime import date, datetime

# ---------- SQLAlchemy Models ----------
class MonthlyPostingDB(Base):
    __tablename__ = "monthly_postings"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String,  nullable=True)

    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #posting
    date = Column(DateTime(timezone=True), nullable=False)

    saving = Column(Float, nullable=False)
    shares = Column(Float, nullable=False)
    social = Column(Float, nullable=False)
    penalty = Column(Float, nullable=False)
    
    loan_interest = Column(Float, nullable=False)
    loan_amount_payment = Column(Float, nullable=False)
    loan_month_repayment = Column(Float, nullable=False)
    
    loan_application = Column(Float, nullable=False)
    
    comments = Column(String, nullable=True)
    
    #approval
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)
    
    approval_levels = Column(Integer, nullable=False)
    
    stage_id = Column(Integer, ForeignKey("list_review_stages.id"), nullable=False)
       
    review1_at = Column(DateTime(timezone=True), nullable=True)
    review1_by = Column(String, nullable=True)
    
    review2_at = Column(DateTime(timezone=True), nullable=True)
    review2_by = Column(String, nullable=True)
    
    review3_at = Column(DateTime(timezone=True), nullable=True)
    review3_by = Column(String, nullable=True)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    #relationships
    user = relationship("UserDB", back_populates="postings", lazy='selectin')
    status = relationship("StatusTypeDB", back_populates="postings", lazy='selectin')
    stage = relationship("ReviewStageDB", back_populates="postings", lazy='selectin')
    transactions = relationship("TransactionDB", back_populates="post", lazy='selectin')
        
# ---------- Pydantic Schemas ----------
class MonthlyPosting(BaseModel):
    #id
    id: Optional[int] = None
    code: Optional[str] = None
    #user
    user_id: int
    #posting
    date: datetime = Field(..., description="The date for the monthly posting")

    saving: float = Field(..., gt=0, description="Saving amount must be greater than zero")
    shares: float = Field(..., gt=0, description="Share amount must be greater than zero")
    social: float = Field(..., gt=0, description="Social amount must be greater than zero")
    penalty: float = Field(..., gt=0, description="Penalty amount must be greater than zero")
    
    loan_interest: float = Field(..., ge=0, description="Loan interest amount must be greater or equal to zero")
    loan_amount_payment: float = Field(..., ge=0, description="Loan payment amount must be greater or equal to zero")
    loan_month_repayment: float = Field(..., ge=0, description="Loan monthly repayment amount must be greater or equal to zero")
    
    loan_application: float = Field(..., ge=0, description="Loan application amount must be greater or equal to zero")
    
    comments: Optional[str] = None
    #approval
    status_id: int = Field(..., ge=1, description="Status must be greater than or equal to 1")
    
    approval_levels: int = Field(..., ge=1, le=3, description="Approval level must be between 1 and 3")
    
    stage_id: int =  Field(..., ge=1, le=3, description="Stage must be between 1 and 3")
    
    review1_at: Optional[datetime] = None
    review1_by: Optional[str] = None
    
    review2_at: Optional[datetime] = None
    review2_by: Optional[str] = None
    
    review3_at: Optional[datetime] = None
    review3_by: Optional[str] = None
    
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]  = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]  = None
    
    class Config:
        orm_mode = True


class MonthlyPostingWithDetail(MonthlyPosting):
    user: User
    stage: ReviewStage
    status: StatusType
    
