from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.osawe.osawedb import Base
from apps.osawe.models.attachment_model import Attachment
from apps.osawe.models.review_stages_model import ReviewStage
from apps.osawe.models.user_model import User, UserSimple
from apps.osawe.models.member_query_type_model import MemberQueryType
from apps.osawe.models.status_types_model import StatusType
from datetime import datetime

# ---------- SQLAlchemy Models ----------
class MemberQueryDB(Base):
    __tablename__ = "member_queries"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String,  nullable=True)
    type_id = Column(Integer, ForeignKey("list_member_query_types.id"), nullable=False)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #attachments
    attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=True)
    
    #query
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    response = Column(String, nullable=True)
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
    user = relationship("UserDB", back_populates="queries", lazy='selectin')
    type = relationship("MemberQueryTypeDB", back_populates="queries", lazy='selectin')
    status = relationship("StatusTypeDB", back_populates="queries", lazy='selectin')
    stage = relationship("ReviewStageDB", back_populates="queries", lazy='selectin')
    attachment = relationship("AttachmentDB", back_populates="queries", lazy='selectin')
# ---------- Pydantic Schemas ----------
class MemberQuery(BaseModel):
    #id
    id: Optional[int] = None
    code: Optional[str] = None
    type_id: int = Field(..., ge=1, description="Type must be greater than or equal to 1")
    
    #user
    user_id: int
    
    #attachments
    attachment_id: Optional[int] = None
    
    #query
    title: str = Field(..., min_length=2, max_length=50, description="Title must be between 2 and 50 characters")
    content: str = Field(..., min_length=10, description="The query must be at least 10 characters")
    response: Optional[str] = None

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


class MemberQueryWithDetail(MemberQuery):
    user: UserSimple
    type: MemberQueryType
    status: StatusType
    stage: ReviewStage
    attachment: Attachment
