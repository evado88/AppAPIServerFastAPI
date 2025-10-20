from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from database import Base
from models.penalty_types_model import PenaltyType
from models.review_stages_model import ReviewStage
from models.transaction_states_model import TransactionState
from models.user_model import User
from models.transaction_types_model import TransactionType
from models.transaction_sources_model import TransactionSource
from models.status_types_model import StatusType
from models.monthly_post_model import MonthlyPosting
from datetime import date, datetime

# ---------- SQLAlchemy Models ----------
class TransactionDB(Base):
    __tablename__ = "transactions"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String,  nullable=True)
    
    #for transactions that target another transaction such as a penalty or loan repayment
    parent_id = Column(Integer, nullable=True)
    
    #type of transaction i.e. saving, loan, penalty payment, etc
    type_id = Column(Integer, ForeignKey("list_transaction_types.id"), nullable=False)
    
    #state of the transaction for loans and penalties i.e. open/closed
    state_id = Column(Integer, ForeignKey("list_transaction_states.id"), nullable=False)
    
    #user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    #transaction
    post_id = Column(Integer, ForeignKey("monthly_postings.id", ondelete="CASCADE"), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)
    source_id = Column(Integer, ForeignKey("list_transaction_sources.id"), nullable=False)
    amount = Column(Float, nullable=False)
    comments = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    
    #loans only
    term_months = Column(Integer, nullable=True)
    interest_rate = Column(Float, nullable=True)
    
    #penalty payment only
    penalty_type_id = Column(Integer, ForeignKey("list_penalty_types.id"), nullable=True)   
    
    #approval
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
    
    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)
    
    #relationships
    user = relationship("UserDB", back_populates="transactions", lazy='selectin')
    type = relationship("TransactionTypeDB", back_populates="transactions", lazy='selectin')
    ptype = relationship("PenaltyTypeDB", back_populates="transactions", lazy='selectin')
    state = relationship("TransactionStateDB", back_populates="transactions", lazy='selectin')
    source = relationship("TransactionSourceDB", back_populates="transactions", lazy='selectin')
    status = relationship("StatusTypeDB", back_populates="transactions", lazy='selectin')
    stage = relationship("ReviewStageDB", back_populates="transactions", lazy='selectin')
    post = relationship("MonthlyPostingDB", back_populates="transactions", lazy='selectin')
# ---------- Pydantic Schemas ----------
class Transaction(BaseModel):
    #id
    id: Optional[int] = None
    code: Optional[str] = None
    
    #for transactions that target another transaction such as a penalty or loan repayment
    parent_id: Optional[int] = None
    
    #type of transaction i.e. saving, loan, penalty payment, etc
    type_id: int = Field(..., ge=1, description="Type must be greater than or equal to 1")
    
    #state of the transaction for loans and penalties i.e. open/close
    state_id: int = Field(..., ge=1, le=2, description="State must be between 1 and 2")
    
    #user
    user_id: int
    
    #transaction
    post_id: Optional[int] = None
    date: datetime = Field(..., description="The date for the transaction")
    source_id: int = Field(..., ge=1, description="Source must be greater than or equal to 1")
    amount: float = Field(..., gt=0, description="Transaction amount must be greater than zero")
    comments: Optional[str] = None
    reference: Optional[str] = None
    
    #loans only
    term_months: Optional[int] = None
    interest_rate: Optional[float] = None
    
    #loans only
    term_months: Optional[int] = None
    
    #penalty payment only
    penalty_type_id: Optional[int] = None
    
    #approval
    status_id: int = Field(..., ge=1, description="Status must be greater than or equal to 1")
    
    approval_levels: int = Field(..., ge=1, le=3, description="Approval level must be between 1 and 3")
   
    stage_id: int =  Field(..., ge=1, le=4, description="Stage must be between 1 and 3")
    
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
    
    model_config = ConfigDict(from_attributes=True)


class TransactionWithDetail(Transaction):
    user: User
    type: TransactionType
    status: StatusType
    state: TransactionState
    source: Optional[TransactionSource] = None
    post: Optional[MonthlyPosting] = None
    ptype : Optional[PenaltyType] = None
    stage: ReviewStage
