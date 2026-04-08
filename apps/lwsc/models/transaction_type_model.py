from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

from apps.lwsc.lwscdb import Base

# ---------- SQLAlchemy Models ----------
class TransactionTypeDB(Base):
    __tablename__ = "transaction_types"

    #id
    id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String,  nullable=False)
    description = Column(String, nullable=True)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default='System')
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    #relationships
    transactions = relationship("TransactionDB", back_populates="type")
    groups = relationship("TransactionGroupDB", back_populates="type")
# ---------- Pydantic Schemas ----------
class TransactionTypeItem(BaseModel):
    #id
    id: int = Field(..., ge=1, description="ID must be greater than or equal to 1")
    type_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    
    class Config:
        orm_mode = True
        
class TransactionType(BaseModel):
    #id
    id: int = Field(..., ge=1, description="ID must be greater than or equal to 1")
    type_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    description: Optional[str] = None
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str] 
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] 
    
    class Config:
        orm_mode = True

