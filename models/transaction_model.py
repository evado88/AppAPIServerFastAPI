from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional
from database import Base
from models.user_model import User
from models.transaction_types_model import TransactionType
from models.transaction_sources_model import TransactionSource
from models.status_types_model import StatusType
from datetime import date, datetime

# ---------- SQLAlchemy Models ----------
class TransactionDB(Base):
    __tablename__ = "transactions"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String,  nullable=True)
    type_id = Column(Integer, ForeignKey("list_transaction_types.id"), nullable=False)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #transaction
    date = Column(DateTime(timezone=True), nullable=False)
    source_id = Column(Integer, ForeignKey("list_transaction_sources.id"), nullable=False)
    amount = Column(Float, nullable=False)
    comments = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    
    #loans only
    term_months = Column(Integer, nullable=True)
    interest_rate = Column(Float, nullable=True)
    
    #approval
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)
    
    approval_levels = Column(Integer, nullable=False)
    
    approved1_at = Column(DateTime(timezone=True), nullable=True)
    approved1_by = Column(String, nullable=True)
    
    approved2_at = Column(DateTime(timezone=True), nullable=True)
    approved2_by = Column(String, nullable=True)
    
    approved3_at = Column(DateTime(timezone=True), nullable=True)
    approved3_by = Column(String, nullable=True)
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    user = relationship("UserDB", back_populates="transactions", lazy='selectin')
    type = relationship("TransactionTypeDB", back_populates="transactions", lazy='selectin')
    source = relationship("TransactionSourceDB", back_populates="transactions", lazy='selectin')
    status = relationship("StatusTypeDB", back_populates="transactions", lazy='selectin')
# ---------- Pydantic Schemas ----------
class Transaction(BaseModel):
    #id
    id: Optional[int] = None
    code: Optional[str] = None
    type_id: int = Field(..., ge=1, description="Type must be greater than or equal to 1")
    #user
    user_id: int
    #transaction
    date: datetime = Field(..., description="The date for the transaction")
    source_id: int = Field(..., ge=1, description="Source must be greater than or equal to 1")
    amount: float = Field(..., gt=0, description="Transaction amount must be greater than zero")
    comments: Optional[str] = None
    reference: Optional[str] = None
    #loans only
    term_months: Optional[int] = None
    interest_rate: Optional[float] = None
    #approval
    status_id: int = Field(..., ge=1, description="Status must be greater than or equal to 1")
    approval_levels: int = Field(..., ge=1, le=3, description="Approval level must be btween 1 and 3")
    approved1_at: Optional[datetime] = None
    approved1_by: Optional[str] = None
    approved2_at: Optional[datetime] = None
    approved2_by: Optional[str] = None
    approved3_at: Optional[datetime] = None
    approved3_by: Optional[str] = None
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]  = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]  = None
    
    class Config:
        orm_mode = True


class TransactionWithDetail(Transaction):
    user: User
    type: TransactionType
    status: StatusType
    source: TransactionSource
