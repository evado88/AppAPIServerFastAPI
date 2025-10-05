from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional
from database import Base
from models.user_model import User
from models.status_types_model import StatusType
from datetime import datetime

# ---------- SQLAlchemy Models ----------
class AttendanceDB(Base):
    __tablename__ = "attendances"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type_id = Column(Integer, ForeignKey("list_attendance_types.id"), nullable=False)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #relationships
    user = relationship("UserDB", back_populates="attendances", lazy='selectin')
    
# ---------- Pydantic Schemas ----------
class Attendance(BaseModel):
    #id
    id: Optional[int] = None
    type_id: int = Field(..., ge=1, description="Type must be greater than or equal to 1")
    
    #user
    user_id: int
    
    class Config:
        orm_mode = True


class AttendanceWithDetail(Attendance):
    user: User
    
