from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from apps.lwsc.lwscdb import Base
from apps.lwsc.models.transaction_type_model import TransactionType
from apps.lwsc.models.user_model import User

# ---------- SQLAlchemy Models ----------
class TransactionGroupDB(Base):
    __tablename__ = "transaction_groups"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # type
    type_id = Column(Integer,  ForeignKey("transaction_types.id"), nullable=False)
    
    # group
    group_name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    transactions = relationship("TransactionDB", back_populates="group")
    user = relationship("UserDB", back_populates="groups", lazy="selectin")
    type = relationship(
        "TransactionTypeDB", back_populates="groups", lazy="selectin"
    )

# ---------- Pydantic Schemas ----------
class TransactionGroup(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # type
    type_id: int
    
    # group
    group_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name must be between 2 and 50 characters",
    )
    description: Optional[str] = None
    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]

    class Config:
        orm_mode = True
        

class TransactionGroupItem(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # type
    type_id: int
    
    # group
    group_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name must be between 2 and 50 characters",
    )
    
    class Config:
        orm_mode = True

class TransactionGroupWithDetail(TransactionGroup):
    type: TransactionType
    user: User
    
class ParamTransactionGroupEdit(BaseModel):
    group: Optional[TransactionGroup] = None
    types: List[TransactionType] = []

    class Config:
        orm_mode = True

