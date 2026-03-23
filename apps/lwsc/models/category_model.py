from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from apps.lwsc.lwscdb import Base
from datetime import datetime
from apps.lwsc.models.user_model import User
from sqlalchemy.dialects.postgresql import JSONB

# ---------- SQLAlchemy Models ----------
class CategoryDB(Base):
    __tablename__ = "categories"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #category
    cat_name = Column(String,  nullable=False)
    description = Column(String, nullable=True)
    rate_list = Column(JSONB, nullable=False)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    user = relationship("UserDB", back_populates="categories", lazy='selectin')
    customer = relationship("CustomerDB", back_populates="category", lazy='selectin')
    billrate = relationship("BillRateDB", back_populates="category", lazy='selectin')
# ---------- Pydantic Schemas ----------
class Category(BaseModel):
    #id
    id: Optional[int] = None
    
    #user
    user_id: int
    
    #query
    cat_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    description: Optional[str] = None
    rate_list: list[dict[str, Any]]= Field(..., description="The attendance list must be provided")
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]  = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]  = None
    
    class Config:
        orm_mode = True
        
class CategoryWithDetail(Category):
    user: User