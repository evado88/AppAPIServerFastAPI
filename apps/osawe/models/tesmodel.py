from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Optional
from apps.osawe.osawedb import Base
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB


# ---------- SQLAlchemy Models ----------
class CategoryDB(Base):
    __tablename__ = "categories"

    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    description = Column(String, nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("list_stages.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("attachments.id"), nullable=False)

    # relationships
    
    user = relationship("UserDB", back_populates="categorys", lazy='selectin')
    status = relationship("StatusDB", back_populates="categorys", lazy='selectin')
    stage = relationship("StageDB", back_populates="categorys", lazy='selectin')
    attachment = relationship("AttachmentDB", back_populates="categorys", lazy='selectin')

class Category(BaseModel):

    id: Optional[int] = None
    user_id: int = Field(..., description="User ID is required")
    name: str = Field(..., description="Name is required")
    description: Optional[str] = None
    status_id: int = Field(..., description="Status ID is required")
    stage_id: int =  Field(..., description="Stage ID is required")
    attachment_id: int = Field(..., description="Attachment ID is required")
    

    class Config:
        orm_mode = True
               