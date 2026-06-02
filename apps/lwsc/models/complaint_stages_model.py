from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.lwsc.lwscdb import Base
from datetime import datetime

# ---------- SQLAlchemy Models ----------
class ComplaintStageDB(Base):
    __tablename__ = "list_complaint_stages"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stage_name = Column(String,  nullable=False)
    description = Column(String, nullable=True)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default='System')
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    complaints = relationship("ComplaintDB", back_populates="complaintstage", lazy="raise")
# ---------- Pydantic Schemas ----------
class ComplaintStage(BaseModel):
    #id
    id: int = Field(..., ge=1, description="ID must be greater than or equal to 1")
    stage_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    description: Optional[str] = None
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str] 
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] 
    
    class Config:
        orm_mode = True

class ComplaintStageItem(BaseModel):
    #id
    id: int = Field(..., ge=1, description="ID must be greater than or equal to 1")
    stage_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    
    class Config:
        orm_mode = True
