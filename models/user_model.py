from sqlalchemy import Column, Integer, String, Float, Date, DateTime,  ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from database import Base

# ---------- SQLAlchemy Models ----------
class UserDB(Base):
    __tablename__ = "users"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String,  nullable=True)
    type = Column(Integer, default=1, nullable=True)
    
    #personal details
    fname = Column(String, nullable=False)
    lname = Column(String, nullable=False)
    mobile1 = Column(String, nullable=False)
    mobile2 = Column(String, nullable=False)
    id_type = Column(String, nullable=False)
    id_no = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    dob = Column(Date, nullable=True)
    
    #guarantor
    guar_fname = Column(String, nullable=False)
    guar_lname = Column(String, nullable=False)
    guar_mobile = Column(String, nullable=False)
    guar_email = Column(String, nullable=False)
    
    #banking
    bank_name = Column(String, nullable=False)
    bank_branch = Column(String, nullable=False)
    bank_acc_name = Column(String, nullable=False)
    bank_acc_no = Column(String, nullable=False)

    #account
    status = Column(Integer, default=1, nullable=False)
    password = Column(String, nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, nullable=True)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    transactions = relationship("TransactionDB", back_populates="user")
    postings = relationship("MonthlyPostingDB", back_populates="user")

# ---------- Pydantic Schemas ----------
class User(BaseModel):
    #id
    id: Optional[int] = None
    code: Optional[str] = None
    type: Optional[int] = None
    #personal details
    fname: str = Field(..., min_length=2, max_length=50, description="First name must be between 2 and 50 characters")
    lname: str = Field(..., min_length=2, max_length=50, description="Last name must be between 2 and 50 characters")
    mobile1: str = Field(..., min_length=3, max_length=15, description="Mobile1 must be between 3 and 15 characters")
    mobile2: str = Field(..., min_length=3, max_length=15, description="Mobile2 must be between 3 and 15 characters")
    id_type: str = Field(..., min_length=3, max_length=20, description="ID type must be between 3 and 20 characters")
    id_no: str = Field(..., min_length=8, max_length=11, description="ID no must be between 8 and 11 characters")
    email: EmailStr
    dob: Optional[date] = None
    #guarantor
    guar_fname: str = Field(..., min_length=2, max_length=50, description="Guarantor first name must be between 2 and 50 characters")
    guar_lname: str = Field(..., min_length=2, max_length=50, description="Guarantor last name must be between 2 and 50 characters")
    guar_mobile: str = Field(..., min_length=3, max_length=15, description="Guarantor mobile must be between 3 and 15 characters")
    guar_email : EmailStr
    #banking
    bank_name: str = Field(..., min_length=3, max_length=50, description="Bank name must be between 3 and 50 characters")
    bank_branch: str = Field(..., min_length=2, max_length=50, description="Bank branch must be between 3 and 50 characters")
    bank_acc_name: str = Field(..., min_length=3, max_length=50, description="Account name must be between 3 and 50 characters")
    bank_acc_no : str = Field(..., min_length=3, max_length=50, description="Account number must be between 3 and 50 characters")
    #account
    status: int =  Field(..., ge=1, description="Status must be greater than or equal to 1")
    password : str = Field(..., min_length=8, max_length=64, description="Password must be between 8 and 64 characters")
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    
    #service columns
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    
    class Config:
        orm_mode = True