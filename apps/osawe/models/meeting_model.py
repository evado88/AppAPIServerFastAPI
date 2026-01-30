from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Optional
from apps.osawe.osawedb import Base
from apps.osawe.models.attachment_model import Attachment
from apps.osawe.models.review_stages_model import ReviewStage
from apps.osawe.models.user_model import User, UserSimple
from apps.osawe.models.status_types_model import StatusType
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

# ---------- SQLAlchemy Models ----------
class MeetingDB(Base):
    __tablename__ = "meetings"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #attachments
    attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=False)
    
    #meeting
    date = Column(DateTime(timezone=True), nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    attendance_list = Column(JSONB, nullable=False)
    
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
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    user = relationship("UserDB", back_populates="meetings", lazy='selectin')
    status = relationship("StatusTypeDB", back_populates="meetings", lazy='selectin')
    attendances = relationship("AttendanceDB", back_populates="meeting", lazy='selectin')
    stage = relationship("ReviewStageDB", back_populates="meetings", lazy='selectin')
    attachment = relationship("AttachmentDB", back_populates="meetings", lazy='selectin')
# ---------- Pydantic Schemas ----------
class Meeting(BaseModel):
    #id
    id: Optional[int] = None
    
    #user
    user_id: int
        
    #attachment
    attachment_id: int = Field(..., ge=1, description="Attachment id must be greater than or equal to 1")
    
    #query
    date: datetime = Field(..., description="The date and time for the meeting")
    title: str = Field(..., min_length=2, max_length=50, description="Title must be between 2 and 50 characters")
    content: str = Field(..., min_length=10, description="The content must be at least 10 characters")
    attendance_list: list[dict[str, Any]]= Field(..., description="The attendance list must be provided")
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
    created_by: Optional[str]  = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]  = None
    
    class Config:
        orm_mode = True

class MeetingSimple(BaseModel):
    #id
    id: Optional[int] = None
    

    #query
    date: datetime = Field(..., description="The date and time for the meeting")
    title: str = Field(..., min_length=2, max_length=50, description="Title must be between 2 and 50 characters")

    #service columns
    created_at: Optional[datetime] = None

    
    class Config:
        orm_mode = True 

class MeetingSimpleWithDetail(MeetingSimple):
    user: UserSimple
    status: StatusType
    stage: ReviewStage
        
class MeetingWithDetail(Meeting):
    user: UserSimple
    attachment: Attachment
    status: StatusType
    stage: ReviewStage
