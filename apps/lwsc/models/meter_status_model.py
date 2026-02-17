from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.lwsc.lwscdb import Base
from datetime import datetime

from apps.lwsc.models.user_model import User

# ---------- SQLAlchemy Models ----------
class MeterStatusDB(Base):
    __tablename__ = "meter_statuses"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #Meter Status
    status_name = Column(String,  nullable=False)
    status_type = Column(String,  nullable=False)
    description = Column(String, nullable=True)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    user = relationship("UserDB", back_populates="meter_statuses", lazy='selectin')
# ---------- Pydantic Schemas ----------
class MeterStatus(BaseModel):
    #id
    id: Optional[int] = None
    
    #user
    user_id: int
    
    #query
    status_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    status_type: str = Field(..., min_length=2, max_length=50, description="Type must be between 2 and 50 characters")
    description: Optional[str] = None
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]  = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]  = None
    
    class Config:
        orm_mode = True

class MeterStatusSimple(BaseModel):
    #id
    id: Optional[int] = None

    #query
    status_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    status_type: str = Field(..., min_length=2, max_length=50, description="Type must be between 2 and 50 characters")
    description: Optional[str] = None
    #service columns
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        
class MeterStatusWithDetail(MeterStatus):
    user: User
