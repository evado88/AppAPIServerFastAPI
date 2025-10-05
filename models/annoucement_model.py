from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional
from database import Base
from models.review_stages_model import ReviewStage
from models.user_model import User
from models.status_types_model import StatusType
from datetime import datetime

# ---------- SQLAlchemy Models ----------
class AnnouncementDB(Base):
    __tablename__ = "announcements"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #query
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    
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
    user = relationship("UserDB", back_populates="announcements", lazy='selectin')
    stage = relationship("ReviewStageDB", back_populates="announcements", lazy='selectin')
    status = relationship("StatusTypeDB", back_populates="announcements", lazy='selectin')
# ---------- Pydantic Schemas ----------
class Announcement(BaseModel):
    #id
    id: Optional[int] = None
    
    #user
    user_id: int
    
    #query
    title: str = Field(..., min_length=2, max_length=50, description="Title must be between 2 and 50 characters")
    content: str = Field(..., min_length=10, description="The content must be at least 10 characters")

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


class AnnouncementWithDetail(Announcement):
    user: User
    status: StatusType
    stage: ReviewStage
    
