from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from database import Base
from models.attachment_model import Attachment
from models.member_model import Member
from models.review_stages_model import ReviewStage
from models.status_types_model import StatusType
from models.user_model import User, UserSimple


# ---------- SQLAlchemy Models ----------
class GuarantorDB(Base):
    __tablename__ = "guarantors"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # user
    user_id = Column(Integer, nullable=False)

    # member
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)

    # guarantor
    guar_fname = Column(String, nullable=False)
    guar_lname = Column(String, nullable=False)
    guar_code = Column(String, nullable=False)
    guar_mobile = Column(String, nullable=False)
    guar_email = Column(String, nullable=False)

    # approval
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)

    approval_levels = Column(Integer, nullable=False)

    stage_id = Column(Integer, ForeignKey("list_review_stages.id"), nullable=False)

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
    member = relationship("MemberDB", back_populates="guarantor", lazy="selectin")
    posting = relationship("MonthlyPostingDB", back_populates="guarantor", lazy="selectin")
    stage = relationship("ReviewStageDB", back_populates="gurantor", lazy="selectin")
    status = relationship("StatusTypeDB", back_populates="gurantor", lazy="selectin")

# ---------- Pydantic Schemas ----------
class Guarantor(BaseModel):
    # id
    id: Optional[int] = None

    # user
    user_id: int = Field(
        ..., ge=1, description="User id must be greater than or equal to 1"
    )
    
    # member
    member_id: Optional[int] = None
    
    # guarantor
    guar_fname: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Guarantor first name must be between 2 and 50 characters",
    )
    guar_lname: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Guarantor last name must be between 2 and 50 characters",
    )
    guar_mobile: str = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Guarantor mobile must be between 3 and 15 characters",
    )
    guar_code: str = Field(
        ...,
        min_length=2,
        max_length=5,
        description="Guarantor code must be between 2 and 5 characters",
    )
    guar_email: EmailStr

   
    # approval
    status_id: int = Field(
        ..., ge=1, le=4, description="Status must be greater than or equal to 1"
    )

    approval_levels: int = Field(
        ..., ge=1, description="Approval levels must be between 1 and 3"
    )

    stage_id: int = Field(..., ge=1, le=8, description="Stage must be between 1 and 8")

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


class GuarantorWithDetail(Guarantor):
    member: Member
    stage: ReviewStage
    status: StatusType
