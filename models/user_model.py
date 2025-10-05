from sqlalchemy import Column, Integer, String, Float, Date, DateTime,  ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from database import Base
from models.review_stages_model import ReviewStage
from models.status_types_model import StatusType

# ---------- SQLAlchemy Models ----------
class UserDB(Base):
    __tablename__ = "users"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String,  nullable=True)
    type = Column(Integer, nullable=True)
    
    #personal details
    fname = Column(String, nullable=False)
    lname = Column(String, nullable=False)
    mobile = Column(String, nullable=False)
    position = Column(String, nullable=True)
    address = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    
    #account
    role = Column(Integer, nullable=False)
    password = Column(String, nullable=False)
            
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("list_review_stages.id"), nullable=False)
    
    approval_levels = Column(Integer, nullable=False)
    
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
    stage = relationship("ReviewStageDB", back_populates="users", lazy='selectin')
    status = relationship("StatusTypeDB", back_populates="users", lazy='selectin')
    transactions = relationship("TransactionDB", back_populates="user")
    postings = relationship("MonthlyPostingDB", back_populates="user")
    config = relationship("SACCOConfigurationDB", back_populates="user")
    announcements = relationship("AnnouncementDB", back_populates="user")
    queries = relationship("MemberQueryDB", back_populates="user")
    notifications = relationship("NotificationDB", back_populates="user")
    attendances = relationship("AttendanceDB", back_populates="user")
    meetings = relationship("MeetingDB", back_populates="user")
    member = relationship("MemberDB", back_populates="user")
    kbarticles = relationship("KnowledgeBaseDB", back_populates="user")
# ---------- Pydantic Schemas ----------
class User(BaseModel):
    #id
    id: Optional[int] = None
    code: Optional[str] = None
    type: Optional[int] = None
    
    #personal details
    fname: str = Field(..., min_length=2, max_length=50, description="First name must be between 2 and 50 characters")
    lname: str = Field(..., min_length=2, max_length=50, description="Last name must be between 2 and 50 characters")
    mobile: str = Field(..., min_length=3, max_length=15, description="Mobile1 must be between 3 and 15 characters")
    position: Optional[str] = None
    address: Optional[str] = None
    email: EmailStr
    
    #account
    role: int =  Field(..., ge=1, le=3, description="Role must be greater than or equal to 1")
    password: str = Field(..., min_length=8, max_length=255, description="Password must be between 8 and 80 characters")
    
    status_id: int =  Field(..., ge=1, description="Status must be greater than or equal to 1")
    stage_id: int =  Field(..., ge=1, le=3, description="Stage must be between 1 and 3")
    
    approval_levels: int = Field(..., ge=1, description="Approval levels must be between 1 and 3")
    
    
    review1_at: Optional[datetime] = None
    review1_by: Optional[str] = None
    
    review2_at: Optional[datetime] = None
    review2_by: Optional[str] = None
    
    review3_at: Optional[datetime] = None
    review3_by: Optional[str] = None
    
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    
    class Config:
        orm_mode = True
        
class UserWithDetail(User):
    stage: ReviewStage
    status: StatusType