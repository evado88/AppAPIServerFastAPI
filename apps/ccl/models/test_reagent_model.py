from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.ccl.ccldb import Base
from datetime import datetime

from apps.ccl.models.reagent_model import Reagent
from apps.ccl.models.test_model import Test
from apps.ccl.models.user_model import User


# ---------- SQLAlchemy Models ----------
class TestReagentDB(Base):
    __tablename__ = "test_reagents"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # test
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    
    # reagent
    reagent_id = Column(Integer, ForeignKey("reagents.id"), nullable=False)
    
    # annual
    test_no = Column(Integer, nullable=False)
    actual_test_no = Column(Float, nullable=False)
    actual_test_cost = Column(Float, nullable=False)
    
    # service columns
    
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    #user = relationship("UserDB", back_populates="test_reagent", lazy="selectin")
    #test = relationship("TestDB", back_populates="test_reagent", lazy="selectin")
    #reagent = relationship("ReagentDB", back_populates="test_reagent", lazy="selectin")
# ---------- Pydantic Schemas ----------
class TestReagent(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # test
    test_id: int
    
    # reagent
    reagent_id: int
    
    # annual
    test_no: int = Field(
        ...,
        ge=0,
        description="Number of tests must be greater or equal to zero",
    )
    actual_test_no: float = Field(
        ...,
        ge=0,
        description="Actual tests in period must be greater or equal to zero",
    )
    actual_test_cost: float = Field(
        ...,
        ge=0,
        description="Annual cost in period must be greater or equal to zero",
    )
    

    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]

    class Config:
        orm_mode = True


class TestReagentWithDetail(TestReagent):
    user: User
    test: Test
    reagent: Reagent
