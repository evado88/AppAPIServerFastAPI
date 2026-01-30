from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from apps.lwsc.lwscdb import Base
from datetime import datetime

from apps.lwsc.models.category_model import Category
from apps.lwsc.models.review_stages_model import ReviewStage
from apps.lwsc.models.town_model import Town
from apps.lwsc.models.walkroute_model import WalkRoute
from apps.lwsc.models.status_types_model import StatusType
from apps.lwsc.models.user_model import User


# ---------- SQLAlchemy Models ----------
class CustomerDB(Base):
    __tablename__ = "customers"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # code
    code = Column(String, nullable=True)
    
    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # cat
    cat_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    # town
    town_id = Column(Integer, ForeignKey("towns.id"), nullable=False)
    
    # route
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    
   # personal details
    fname = Column(String, nullable=False)
    lname = Column(String, nullable=False)
    title = Column(String, nullable=True)
    
    #contact, address 
    email = Column(String, unique=True, index=True, nullable=False)
    mobile = Column(String, nullable=False)
    tel = Column(String, nullable=False)
    address_physical = Column(String, nullable=True)
    address_postal = Column(String, nullable=True)
    
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    
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

    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    user = relationship("UserDB", back_populates="customers", lazy="selectin")
    stage = relationship("ReviewStageDB", back_populates="customers", lazy="selectin")
    status = relationship("StatusTypeDB", back_populates="customers", lazy="selectin")
    route = relationship("WalkRouteDB", back_populates="customer", lazy="selectin")
    category = relationship("CategoryDB", back_populates="customer", lazy="selectin")
    town = relationship("TownDB", back_populates="customer", lazy="selectin")
    meters = relationship("MeterDB", back_populates="customer", lazy="selectin")
    meterreadings = relationship("MeterReadingDB", back_populates="customer", lazy="selectin") 
# ---------- Pydantic Schemas ----------
class CustomerSimple(BaseModel):
    # id
    id: Optional[int] = None

    # town
    town_id: int
    
    # personal details
    fname: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="First name must be between 2 and 50 characters",
    )
    lname: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Last name must be between 2 and 50 characters",
    )
    #contact, address 
    mobile: str = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Mobile must be between 3 and 15 characters",
    )
    address_physical: Optional[str] = None
    
    class Config:
        orm_mode = True
        
class Customer(BaseModel):
    # id
    id: Optional[int] = None
    
    # codd
    code: Optional[str] = None
    
    # user
    user_id: int
    
    # cat
    cat_id: int

    # town
    town_id: int
    
    # route
    route_id: int

    # personal details
    fname: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="First name must be between 2 and 50 characters",
    )
    lname: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Last name must be between 2 and 50 characters",
    )
    title: Optional[str] = None
    
    #contact, address 
    email:  Optional[EmailStr] = None
    mobile: str = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Mobile must be between 3 and 15 characters",
    )
    tel: Optional[str] = None
    address_physical: Optional[str] = None
    address_postal: Optional[str] = None
    
    lat: Optional[float] = None
    lon: Optional[float] = None
    
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
    created_by: Optional[str]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]

    class Config:
        orm_mode = True

class CustomerWithDetail(Customer):
    user: User
    category: Category
    town: Town
    route: WalkRoute
    stage : ReviewStage
    status: StatusType