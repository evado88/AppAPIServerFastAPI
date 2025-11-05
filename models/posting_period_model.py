from sqlalchemy import Column, Date, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from database import Base
from datetime import datetime

from models.review_stages_model import ReviewStage
from models.status_types_model import StatusType

# ---------- SQLAlchemy Models ----------
class PostingPeriodDB(Base):
    __tablename__ = "list_posting_periods"

    #id
    id = Column(Integer, primary_key=True, index=True)
    
    period_name = Column(String,  nullable=False)
    description = Column(String, nullable=True)
    
    #period
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    
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
    postings = relationship("MonthlyPostingDB", back_populates="period")
    stage = relationship("ReviewStageDB", back_populates="periods", lazy='selectin')
    status = relationship("StatusTypeDB", back_populates="periods", lazy='selectin')
# ---------- Pydantic Schemas ----------
class PostingPeriod(BaseModel):
    #id
    id: int = Field(..., ge=1, description="ID must be greater than or equal to 1")
    period_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    description: Optional[str] = None
    
    #period
    month: int = Field(..., ge=1, le=12, description="Period month must be between 1 and 12")
    year: int = Field(..., ge=2025, le=2026, description="Period year must be between 2025 and 2026")
    
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