from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.lwsc.lwscdb import Base
from datetime import datetime

from apps.lwsc.models.category_model import Category
from apps.lwsc.models.review_stages_model import ReviewStage
from apps.lwsc.models.district_model import District
from apps.lwsc.models.walkroute_model import WalkRoute
from apps.lwsc.models.status_types_model import StatusType
from apps.lwsc.models.user_model import User


# ---------- SQLAlchemy Models ----------
class BillRateDB(Base):
    __tablename__ = "bill_rates"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # cat
    cat_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    # band
    order = Column(Integer,  nullable=False)
    name = Column(String, nullable=False)
    
    from_vol = Column(Float, nullable=False)
    to_vol = Column(Float, nullable=False)
    rate = Column(Float, nullable=False)
    
    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")

    # relationships
    user = relationship("UserDB", back_populates="billrate", lazy="selectin")
    category = relationship("CategoryDB", back_populates="billrate", lazy="selectin")
    
# ---------- Pydantic Schemas ----------
class BillRate(BaseModel):
    # id
    id: Optional[int] = None

    # user
    user_id: int
    
    # cat
    cat_id: int

    # band
    order:  int = Field(
        ...,
        min=0,
        description="The order must be greater than or equal to zero",
    )

    name:  str = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Name must be between 3 and 15 characters",
    )

    from_vol: float = Field(
        ...,
        min=0,
        description="The from volume must be greater than or equal to zero",
    )
    to_vol: float = Field(
        ...,
        min=0,
        description="The to volume must be greater than or equal to zero",
    )
    rate: float = Field(
        ...,
        min=0,
        description="The rate must be greater than or equal to zero",
    )
    
    
    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]
    
    class Config:
        orm_mode = True

class BillRateWithDetail(BillRate):
    user: User
    category: Category