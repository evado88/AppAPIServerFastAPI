from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from database import Base
from datetime import datetime

# ---------- SQLAlchemy Models ----------
class PenaltyTypeDB(Base):
    __tablename__ = "list_penalty_types"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type_name = Column(String,  nullable=False)
    description = Column(String, nullable=True)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default='System')
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    transactions = relationship("TransactionDB", back_populates="ptype")
# ---------- Pydantic Schemas ----------
class PenaltyType(BaseModel):
    #id
    id: int = Field(..., ge=1, description="ID must be greater than or equal to 1")
    type_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    description: Optional[str] = None
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str] 
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] 
    
    model_config = ConfigDict(from_attributes=True)

