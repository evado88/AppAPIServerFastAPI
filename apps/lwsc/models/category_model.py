from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from apps.lwsc.lwscdb import Base
from datetime import datetime
from apps.lwsc.models.review_stages_model import ReviewStageItem
from apps.lwsc.models.status_types_model import StatusTypeItem
from apps.lwsc.models.user_model import User, UserSimple
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
    user = relationship("UserDB", back_populates="categories", lazy="raise")
    stage = relationship("ReviewStageDB", back_populates="category", lazy="raise")
    status = relationship("StatusTypeDB", back_populates="category", lazy="raise")
    customer = relationship("CustomerDB", back_populates="category", lazy="raise")
    billrate = relationship("BillRateDB", back_populates="category", lazy="raise")
    
# ---------- Pydantic Schemas ----------
class Category(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # query
    cat_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    description: Optional[str] = None
    rate_list: list[dict[str, Any]]= Field(..., description="The attendance list must be provided")
    
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
    
    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]  = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]  = None
    
    class Config:
        orm_mode = True

class CategoryItem(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # category
    cat_name: str = Field(..., min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    
    class Config:
        orm_mode = True
        
class CategoryWithDetail(Category):
    user: UserSimple
    stage : ReviewStageItem
    status: StatusTypeItem