from sqlalchemy import Column, Date, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from database import Base
from datetime import datetime, date

from models.review_stages_model import ReviewStage
from models.status_types_model import StatusType

# ---------- SQLAlchemy Models ----------
class PostingPeriodDB(Base):
    __tablename__ = "list_posting_periods"

    #id
    id = Column(String, primary_key=True, index=True)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    #attachments
    attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=True)
    
    #period
    period_name = Column(String,  nullable=False)
    description = Column(String, nullable=True)
    
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    
    #accounts
    cash_at_bank = Column(Float, nullable=False)
    
    #configuration for period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    posting_date_start = Column(Date, nullable=False)
    posting_date_end = Column(Date, nullable=False)
    
    late_posting_date_start = Column(Date, nullable=False)
    late_posting_date_end = Column(Date, nullable=False)
    
    mid_posting_date_start = Column(Date, nullable=False)
    mid_posting_date_end = Column(Date, nullable=False)
    
    saving_multiple = Column(Float, nullable=False)
    shares_multiple  = Column(Float, nullable=False)
    social_min = Column(Float, nullable=False)
    
    loan_interest_rate = Column(Float, nullable=False)
    loan_repayment_rate = Column(Float, nullable=False)
    loan_saving_ratio = Column(Float, nullable=False)
    
    loan_duration = Column(Integer, nullable=False)
    loan_apply_limit = Column(Integer, nullable=False)
    
    late_posting_rate = Column(Float, nullable=False)
    incorrect_posting_rate = Column(Float, nullable=False)
    missed_meeting_rate = Column(Float, nullable=False)
    late_meeting_rate = Column(Float, nullable=False)

    #approval
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
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default='System')
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    #relationships
    user = relationship("UserDB", back_populates="periods", lazy='selectin')
    postings = relationship("MonthlyPostingDB", back_populates="period")
    stage = relationship("ReviewStageDB", back_populates="periods", lazy='selectin')
    status = relationship("StatusTypeDB", back_populates="periods", lazy='selectin')
    attachment = relationship("AttachmentDB", back_populates="period", lazy='selectin')
# ---------- Pydantic Schemas ----------
class PostingPeriod(BaseModel):
    #id
    id:  Optional[int] = None
    
    #user
    user_id: Optional[int] = None
        
    #attachment
    attachment_id: Optional[int] = None
    
    #period
    period_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    description: Optional[str] = None
    
   
    month: int = Field(..., ge=1, le=12, description="Period month must be between 1 and 12")
    year: int = Field(..., ge=2025, le=2026, description="Period year must be between 2025 and 2026")
    
    #accounts
    cash_at_bank: float = Field(..., ge=0, description="The cash at bank must be greater than or equal to zero")
    
    #configurations for period
    period_start: date = Field(..., description="The start date for the period")
    period_end: date = Field(..., description="The end date for the period")

    posting_date_start: date = Field(..., description="The start date for posting before late fees are applied")
    posting_date_end: date = Field(..., description="The end date for posting before late fees are applied")
    
    late_posting_date_start: date = Field(..., description="The start date for posting when late fees are applied")
    late_posting_date_end: date = Field(..., description="The end date for posting when late fees are applied")
    
    mid_posting_date_start: date = Field(..., description="The start date for posting for mid-month posting")
    mid_posting_date_end: date = Field(..., description="The end date for posting for mid-month posting")

    saving_multiple: float = Field(..., gt=0, description="The multiple for savings must be greater than zero")
    shares_multiple: float = Field(..., gt=0, description="The multiple for shares must be greater than zero")
    social_min: float = Field(..., ge=0, description="The social amount must be greater or equal to zero")
   
    loan_interest_rate: float = Field(..., ge=0, description="The loan interest rate must be greater than zero")
    loan_repayment_rate: float = Field(..., ge=0, description="The loan repayment rate must be greater than zero")
    loan_saving_ratio: float = Field(..., gt=0, description="The loan saving ratio must be greater than zero")
    
    loan_duration: float = Field(..., ge=1, le=12, description="The loan duration must be between 1 and 12")
    loan_apply_limit: float = Field(..., ge=0, description="The loan apply limit must be greater or equal to zero")
         
    late_posting_rate: float = Field(..., ge=0, description="The late posting rate must be greater than zero")
    incorrect_posting_rate: float = Field(..., ge=0, description="The incorrect posting rate must be greater than zero")
    missed_meeting_rate: float = Field(..., ge=0, description="The missed meeting rate must be greater than zero")
    late_meeting_rate: float = Field(..., gt=0, description="The late meeting rate must be greater than zero")
    
    #approval
    status_id: int = Field(..., ge=1, description="Status must be greater than or equal to 1")
    
    approval_levels: int = Field(..., ge=1, le=3, description="Approval level must be between 1 and 3")
    
    stage_id: int =  Field(..., ge=1, le=8, description="Stage must be between 1 and 8")
        
    review1_at: Optional[datetime] = None
    review1_by: Optional[str] = None
    review1_comments: Optional[str] = None
        
    review2_at: Optional[datetime] = None
    review2_by: Optional[str] = None
    review2_comments: Optional[str] = None
        
    review3_at: Optional[datetime] = None
    review3_by: Optional[str] = None
    review3_comments: Optional[str] = None
    
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str] 
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] 
    
    class Config:
        orm_mode = True

class PostingPeriodWithDetail(PostingPeriod):
    status: StatusType
    stage: ReviewStage