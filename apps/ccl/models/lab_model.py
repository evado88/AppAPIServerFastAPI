from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.ccl.ccldb import Base
from datetime import datetime

from apps.ccl.models.user_model import User


# ---------- SQLAlchemy Models ----------
class LabDB(Base):
    __tablename__ = "labs"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    user = relationship("UserDB", back_populates="labs", lazy="selectin")
    tests = relationship("TestDB", back_populates="lab", lazy="selectin")
# ---------- Pydantic Schemas ----------
class Lab(BaseModel):
    # id
    id: Optional[int] = None
    # user
    user_id: int

    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name must be between 2 and 50 characters",
    )
    description: Optional[str] = None
    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]

    class Config:
        orm_mode = True

class LabWithDetail(Lab):
    user: User