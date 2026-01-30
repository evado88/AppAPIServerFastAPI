from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.osawe.osawedb import Base
from apps.osawe.models.user_model import User, UserSimple
from apps.osawe.models.status_types_model import StatusType
from datetime import datetime

# ---------- SQLAlchemy Models ----------
class NotificationDB(Base):
    __tablename__ = "notifications"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #query
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    
    #approval
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, default='System', nullable=True)
    
    #relationships
    user = relationship("UserDB", back_populates="notifications", lazy='selectin')
    status = relationship("StatusTypeDB", back_populates="notifications", lazy='selectin')
# ---------- Pydantic Schemas ----------
class Notification(BaseModel):
    #id
    id: Optional[int] = None
    
    #user
    user_id: int
    
    #query
    title: str = Field(..., min_length=2, max_length=50, description="Title must be between 2 and 50 characters")
    content: str = Field(..., min_length=10, description="The content must be at least 10 characters")

    #approval
    status_id: int = Field(..., ge=1, description="Status must be greater than or equal to 1")
    
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]  = None
    
    class Config:
        orm_mode = True


class NotificationWithDetail(Notification):
    user: UserSimple
    status: StatusType
    
