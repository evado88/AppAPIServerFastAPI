from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.osawe.osawedb import Base
from datetime import datetime


# ---------- SQLAlchemy Models ----------
class TransactionGroupDB(Base):
    __tablename__ = "list_transaction_groups"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

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


# ---------- Pydantic Schemas ----------
class TransactionGroup(BaseModel):
    # id
    id: Optional[int] = None
    # user
    user_id: int

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
