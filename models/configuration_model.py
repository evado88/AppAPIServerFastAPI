from sqlalchemy import Column, Integer, String, DateTime, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from database import Base
from models.user_model import User
from datetime import date, datetime

# ---------- SQLAlchemy Models ----------
class SACCOConfigurationDB(Base):
    __tablename__ = "configuration"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #configurations
    posting_date_max = Column(Date, nullable=False)
    
    saving_multiple = Column(Float, nullable=False)
    shares_multiple  = Column(Float, nullable=False)
    social_min = Column(Float, nullable=False)
    loan_interest_rate = Column(Float, nullable=False)
    loan_repayment_rate = Column(Float, nullable=False)
    loan_saving_ratio = Column(Float, nullable=False)
    
    late_posting_rate = Column(Float, nullable=False)
    missed_meeting_rate = Column(Float, nullable=False)
    late_meeting_rate = Column(Float, nullable=False)
    
    #service columns
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    user = relationship("UserDB", back_populates="config", lazy='selectin')
# ---------- Pydantic Schemas ----------
class SACCOConfiguration(BaseModel):
    #id
    id: Optional[int] = None
    #user
    user_id: int
    #configurations
    posting_date_max: date = Field(..., description="The maximum date for posting before late fees are applied")
    
    saving_multiple: float = Field(..., gt=0, description="The multiple for savings must be greater than zero")
    shares_multiple: float = Field(..., gt=0, description="The multiple for shares must be greater than zero")
    social_min: float = Field(..., ge=0, description="The social amount must be greater or equal to zero")
   
    loan_interest_rate: float = Field(..., ge=0, description="The loan interest rate must be greater than zero")
    loan_repayment_rate: float = Field(..., ge=0, description="The loan repayment rate must be greater than zero")
    loan_saving_ratio: float = Field(..., gt=0, description="The loan saving ratio must be greater than zero")
    
    late_posting_rate: float = Field(..., ge=0, description="The late posting rate must be greater than zero")
    missed_meeting_rate: float = Field(..., ge=0, description="The missed meeting rate must be greater than zero")
    late_meeting_rate: float = Field(..., gt=0, description="The late meeting rate must be greater than zero")
    

    #service columns
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]  = None
    
    model_config = ConfigDict(from_attributes=True)

class SACCOConfigurationWithDetail(SACCOConfiguration):
    user: User
    
