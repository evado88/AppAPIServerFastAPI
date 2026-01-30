from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.lwsc.lwscdb import Base
from datetime import datetime

from apps.lwsc.models.review_stages_model import ReviewStage
from apps.lwsc.models.status_types_model import StatusType
from apps.lwsc.models.user_model import User

# ---------- SQLAlchemy Models ----------
class TownDB(Base):
    __tablename__ = "towns"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #town
    name = Column(String,  nullable=False)
    code = Column(String,  nullable=False)
    description = Column(String, nullable=True)
    
    # approval
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("list_review_stages.id"), nullable=False)

    approval_levels = Column(Integer, nullable=False)

    review1_at = Column(DateTime(timezone=True), nullable=True)
    review1_by = Column(String, nullable=True)
    review1_comments = Column(String, nullable=True)

    review2_at = Column(DateTime(timezone=True), nullable=True)
    review2_by = Column(String, nullable=True)
    review2_comments = Column(String, nullable=True)

    review3_at = Column(DateTime(timezone=True), nullable=True)
    review3_by = Column(String, nullable=True)
    review3_comments = Column(String, nullable=True)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    user = relationship("UserDB", back_populates="towns", lazy='selectin')
    meters = relationship("MeterDB", back_populates="town", lazy='selectin')
    customer = relationship("CustomerDB", back_populates="town", lazy='selectin')
    routes = relationship("WalkRouteDB", back_populates="town", lazy='selectin')
    stage = relationship("ReviewStageDB", back_populates="towns", lazy="selectin")
    status = relationship("StatusTypeDB", back_populates="towns", lazy="selectin")
    
# ---------- Pydantic Schemas ----------
class TownSimple(BaseModel):
    #id
    id: Optional[int] = None
    #query
    name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    code: str = Field(..., min_length=3, max_length=3, description="Code must be 3 characters")
    
    class Config:
        orm_mode = True

class Town(BaseModel):
    #id
    id: Optional[int] = None
    
    #user
    user_id: int
    
    #query
    name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    code: str = Field(..., min_length=3, max_length=3, description="Code must be 3 characters")
    description: Optional[str] = None
    
    # approval
    status_id: int = Field(
        ..., ge=1, description="Status must be greater than or equal to 1"
    )
    stage_id: int = Field(..., ge=1, le=8, description="Stage must be between 1 and 8")

    approval_levels: int = Field(
        ..., ge=1, le=3, description="Approval levels must be between 1 and 3"
    )

    review1_at: Optional[datetime] = None
    review1_by: Optional[str] = None
    review1_comments: Optional[str] = None

    review2_at: Optional[datetime] = None
    review2_by: Optional[str] = None
    review2_comments: Optional[str] = None

    review3_at: Optional[datetime] = None
    review3_by: Optional[str] = None
    review3_comments: Optional[str] = None
    
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]  = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]  = None
    
    class Config:
        orm_mode = True
        
class TownWithDetail(Town):
    user: User
    stage : ReviewStage
    status: StatusType