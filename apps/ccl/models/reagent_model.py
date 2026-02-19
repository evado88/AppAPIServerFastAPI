from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.ccl.ccldb import Base
from datetime import datetime

from apps.ccl.models.user_model import User


# ---------- SQLAlchemy Models ----------
class ReagentDB(Base):
    __tablename__ = "reagents"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # details
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # costs
    cost = Column(Float, nullable=False)
    
    expiry_period = Column(Float, nullable=False)
    generic_reagent_unit = Column(String, nullable=False) #ml
    quantity_per_gru = Column(Float, nullable=False)
    tests_per_gru = Column(Float, nullable=False)
    
    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    user = relationship("UserDB", back_populates="reagents", lazy="selectin")
    #test_reagent = relationship("TestReagentDB", back_populates="reagent", lazy="selectin")
# ---------- Pydantic Schemas ----------
class Reagent(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # details
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name must be between 2 and 50 characters",
    )
    description: Optional[str] = None
    
    # costs
    cost: float = Field(..., ge=0, description="The cost must be greater or equal to zero")
    expiry_period: float = Field(..., ge=0, description="The expiry_period cost must be greater or equal to zero")
    generic_reagent_unit: str = Field(..., description="The generic reagent unit (e.g., ml)")
    quantity_per_gru: float = Field(..., ge=0, description="The quantity of reagent per generic reagent unit")
    tests_per_gru: float = Field(..., ge=0, description="The number of tests per generic reagent unit")
  
    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]

    class Config:
        orm_mode = True

class ReagentWithDetail(Reagent):
    user: User