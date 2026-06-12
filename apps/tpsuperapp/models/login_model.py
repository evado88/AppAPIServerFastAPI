from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

from apps.tpsuperapp.tpsuperappdb import Base

# ---------- SQLAlchemy Models ----------
class LoginDB(Base):
    __tablename__ = "user_logins"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String,  nullable=False)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default='System')
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

# ---------- Pydantic Schemas ----------
class Login(BaseModel):
    #id
    id: Optional[int] = None 
    username: str = Field(..., description="Username is required")
    
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str] 
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] 
    
    class Config:
        orm_mode = True


