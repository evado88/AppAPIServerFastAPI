from sqlalchemy import Column, Integer, String, Float, Date, DateTime,  ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from database import Base
from models.review_stages_model import ReviewStage
from models.status_types_model import StatusType
from models.user_model import User

# ---------- SQLAlchemy Models ----------
class MemberDB(Base):
    __tablename__ = "members"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    number = Column(String,  nullable=True)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #personal details
    fname = Column(String, nullable=False)
    lname = Column(String, nullable=False)
    mobile1 = Column(String, nullable=False)
    mobile2 = Column(String, nullable=False)
    id_type = Column(String, nullable=False)
    id_no = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    dob = Column(Date, nullable=True)
    
    #guarantor
    guar_fname = Column(String, nullable=False)
    guar_lname = Column(String, nullable=False)
    guar_mobile = Column(String, nullable=False)
    guar_email = Column(String, nullable=False)
    
    #banking
    bank_name = Column(String, nullable=False)
    bank_branch = Column(String, nullable=False)
    bank_acc_name = Column(String, nullable=False)
    bank_acc_no = Column(String, nullable=False)

    #account
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
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    user = relationship("UserDB", back_populates="member", lazy='selectin')
    stage = relationship("ReviewStageDB", back_populates="members", lazy='selectin')
    status = relationship("StatusTypeDB", back_populates="members", lazy='selectin')
    
# ---------- Pydantic Schemas ----------
class Member(BaseModel):
    #id
    id: Optional[int] = None
    number: Optional[str] = None
    
    #personal details
    fname: str = Field(..., min_length=2, max_length=50, description="First name must be between 2 and 50 characters")
    lname: str = Field(..., min_length=2, max_length=50, description="Last name must be between 2 and 50 characters")
    mobile1: str = Field(..., min_length=3, max_length=15, description="Mobile1 must be between 3 and 15 characters")
    mobile2: str = Field(..., min_length=3, max_length=15, description="Mobile2 must be between 3 and 15 characters")
    id_type: str = Field(..., min_length=3, max_length=20, description="ID type must be between 3 and 20 characters")
    id_no: str = Field(..., min_length=8, max_length=11, description="ID no must be between 8 and 11 characters")
    email: EmailStr
    dob: Optional[date] = None
    
    #guarantor
    guar_fname: str = Field(..., min_length=2, max_length=50, description="Guarantor first name must be between 2 and 50 characters")
    guar_lname: str = Field(..., min_length=2, max_length=50, description="Guarantor last name must be between 2 and 50 characters")
    guar_mobile: str = Field(..., min_length=3, max_length=15, description="Guarantor mobile must be between 3 and 15 characters")
    guar_email : EmailStr
    
    #banking
    bank_name: str = Field(..., min_length=3, max_length=50, description="Bank name must be between 3 and 50 characters")
    bank_branch: str = Field(..., min_length=2, max_length=50, description="Bank branch must be between 3 and 50 characters")
    bank_acc_name: str = Field(..., min_length=3, max_length=50, description="Account name must be between 3 and 50 characters")
    bank_acc_no : str = Field(..., min_length=3, max_length=50, description="Account number must be between 3 and 50 characters")
    
    #account
    status_id: int =  Field(..., ge=1, le=3, description="Status must be greater than or equal to 1")

    approval_levels: int = Field(..., ge=1, description="Approval levels must be between 1 and 3")
    
    stage_id: int =  Field(..., ge=1, le=3, description="Stage must be between 1 and 3")
    
    
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
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
        
class MemberWithDetail(Member):
    user: User
    stage: ReviewStage
    status: StatusType

