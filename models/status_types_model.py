from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from database import Base
from datetime import datetime

# ---------- SQLAlchemy Models ----------
class StatusTypeDB(Base):
    __tablename__ = "list_status_types"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status_name = Column(String,  nullable=False)
    description = Column(String, nullable=True)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default='System')
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    transactions = relationship("TransactionDB", back_populates="status")
    postings = relationship("MonthlyPostingDB", back_populates="status")
    queries = relationship("MemberQueryDB", back_populates="status")
    notifications = relationship("NotificationDB", back_populates="status")
    announcements = relationship("AnnouncementDB", back_populates="status")
    meetings = relationship("MeetingDB", back_populates="status")
    members = relationship("MemberDB", back_populates="status")
    users = relationship("UserDB", back_populates="status")
    kbarticles = relationship("KnowledgeBaseDB", back_populates="status")
    periods = relationship("PostingPeriodDB", back_populates="status")
# ---------- Pydantic Schemas ----------
class StatusType(BaseModel):
    #id
    id: int = Field(..., ge=1, description="ID must be greater than or equal to 1")
    status_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    description: Optional[str] = None
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str] 
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] 
    
    class Config:
        orm_mode = True

