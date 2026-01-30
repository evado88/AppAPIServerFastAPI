from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.lwsc.lwscdb import Base
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
    users = relationship("UserDB", back_populates="status")
    towns = relationship("TownDB", back_populates="status")
    routes = relationship("WalkRouteDB", back_populates="status")
    customers = relationship("CustomerDB", back_populates="status")
    meters = relationship("MeterDB", back_populates="status")
    meterreadings = relationship("MeterReadingDB", back_populates="status")
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

