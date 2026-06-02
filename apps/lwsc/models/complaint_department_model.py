from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from apps.lwsc.lwscdb import Base
from datetime import datetime
from apps.lwsc.models.review_stages_model import ReviewStageItem
from apps.lwsc.models.status_types_model import StatusTypeItem
from apps.lwsc.models.user_model import User, UserSimple
from sqlalchemy.dialects.postgresql import JSONB

# ---------- SQLAlchemy Models ----------
class ComplaintDepartmentDB(Base):
    __tablename__ = "complaint_departments"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #category
    dept_name = Column(String,  nullable=False)
    description = Column(String, nullable=True)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    user = relationship("UserDB", back_populates="departments", lazy="raise")
    complaints = relationship("ComplaintDB", back_populates="department", lazy="raise")
    
# ---------- Pydantic Schemas ----------
class ComplaintDepartment(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # query
    dept_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    description: Optional[str] = None

    
    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]  = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]  = None
    
    class Config:
        orm_mode = True

class ComplaintDepartmentItem(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # category
    dept_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    
    class Config:
        orm_mode = True
        
class ComplaintDepartmentWithDetail(ComplaintDepartment):
    user: UserSimple