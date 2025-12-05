from sqlalchemy import Column, Integer, String, DateTime, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from database import Base
from datetime import date, datetime

# ---------- SQLAlchemy Models ----------
class AttachmentDB(Base):
    __tablename__ = "attachments"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # file
    name = Column(String, nullable=True)
    path = Column(String, nullable=True)
    filesize = Column(Integer, nullable=True)
    filetype = Column(String, nullable=True)
    
    # linkage
    parent = Column(Integer, nullable=True)
    type = Column(String, nullable=True)
    
    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    meetings = relationship("MeetingDB", back_populates="attachment")
    member = relationship("MemberDB", back_populates="attachment")
    post = relationship("MonthlyPostingDB", back_populates="attachment")
    announcements = relationship("AnnouncementDB", back_populates="attachment")
    kbarticles = relationship("KnowledgeBaseDB", back_populates="attachment")
    queries = relationship("MemberQueryDB", back_populates="attachment")
    period = relationship("PostingPeriodDB", back_populates="attachment")
    transaction = relationship("TransactionDB", back_populates="attachment")
# ---------- Pydantic Schemas ----------
class Attachment(BaseModel):
    # id
    id: Optional[int] = None

    # file
    name: Optional[str] = None
    path: Optional[str] = None
    filesize: Optional[int] = None
    filetype: Optional[str] = None
    
    # linkage
    parent: Optional[int] = None
    type: Optional[str] = None
    
    created_at: Optional[datetime] = None
    created_by: Optional[str]  = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        orm_mode = True
        
# ---------- Pydantic Schemas ----------
class AttachmentInput(BaseModel):
    # linkage
    parent: Optional[int] = None
    type: Optional[str] = None
    
    class Config:
        orm_mode = True