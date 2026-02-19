from modulefinder import test
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from apps.ccl.ccldb import Base


# ---------- SQLAlchemy Models ----------
class UserDB(Base):
    __tablename__ = "users"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String, nullable=True)
    type = Column(Integer, nullable=True)

    # personal details
    fname = Column(String, nullable=False)
    lname = Column(String, nullable=False)
    position = Column(String, nullable=True)
    
    #contact, address 
    email = Column(String, unique=True, index=True, nullable=False)
    mobile_code = Column(String, nullable=False)
    mobile = Column(String, nullable=False)
    address_physical = Column(String, nullable=True)
    address_postal = Column(String, nullable=True)

    # account
    role = Column(Integer, nullable=False)
    password = Column(String, nullable=False)

    # approval
    status_id = Column(Integer, nullable=False)
    stage_id = Column(Integer, nullable=False)

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
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    labs = relationship("LabDB", back_populates="user")
    tests = relationship("TestDB", back_populates="user")
    instruments = relationship("InstrumentDB", back_populates="user")
    reagents = relationship("ReagentDB", back_populates="user")
    #test_instrument = relationship("TestInstrumentDB", back_populates="user")
    #test_reagent = relationship("TestReagentDB", back_populates="user")
# ---------- Pydantic Schemas ----------
class User(BaseModel):
    # id
    id: Optional[int] = None
    
    user_id: Optional[int] = None
    
    code: Optional[str] = None
    type: Optional[int] = None
    
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
    position: Optional[str] = None
    
    #contact, address 
    email: EmailStr
    mobile_code: str = Field(
        ...,
        min_length=2,
        max_length=5,
        description="Mobile code must be between 3 and 15 characters",
    )
    mobile: str = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Mobile must be between 3 and 15 characters",
    )
    address_physical: Optional[str] = None
    address_postal: Optional[str] = None
    
    # account
    role: int = Field(
        ..., ge=1, le=3, description="Role must be greater than or equal to 1"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Password must be between 8 and 80 characters",
    )
    
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
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        orm_mode = True

# ---------- Pydantic Schemas ----------
# user that hides unnecessary fields
class UserSimple(BaseModel):
    # id
    id: Optional[int] = None

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
    email: EmailStr
    mobile: str = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Mobile must be between 3 and 15 characters",
    )

    class Config:
        orm_mode = True

class UserWithDetail(User):
    pass




