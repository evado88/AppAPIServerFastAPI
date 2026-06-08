from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

from apps.ccl.ccldb import Base

# ---------- SQLAlchemy Models ----------
class MonthDB(Base):
    __tablename__ = "list_months"

    #id
    id = Column(Integer, primary_key=True, index=True)
    month_name = Column(String,  nullable=False)
    description = Column(String, nullable=True)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default='System')
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    testpricevolumes = relationship("TestPriceVolmeDB", back_populates="month", lazy="raise")
# ---------- Pydantic Schemas ----------
class Month(BaseModel):
    #id
    id: int = Field(..., ge=1, le=12, description="Month ID must be between 1 and 12")
    month_name: str = Field(..., min_length=3, max_length=50, description="Month name must be between 3 and 50 characters")
    description: Optional[str] = None
    
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str] 
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] 
    
    class Config:
        orm_mode = True


