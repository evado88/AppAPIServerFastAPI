from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Any, Optional
from database import Base
from models.attachment_model import Attachment
from models.review_stages_model import ReviewStage
from models.user_model import User, UserSimple
from models.status_types_model import StatusType
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

# ---------- SQLAlchemy Models ----------
class AuditDB(Base):
    __tablename__ = "audits"

    #id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    #user
    user_id = Column(Integer, nullable=False)
    user_email = Column(String, nullable=False)
    token = Column(String, nullable=False)
    
    #audit
    date = Column(DateTime(timezone=True), nullable=False)
    feature = Column(String, nullable=False)
    model = Column(String, nullable=True)
    object_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    before = Column(JSONB, nullable=True)
    after = Column(JSONB, nullable=True)

    #service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True)
    
# ---------- Pydantic Schemas ----------
class Audit(BaseModel):
    #id
    id: Optional[int] = None
    
    #user
    user_id: int
    user_email: EmailStr
    token: str = Field(..., description="The token for the audit is required")
    
    #audit
    date: datetime = Field(..., description="The date and time for the audit is required")
    feature: str = Field(..., description="The feature for the audit is required")
    model: Optional[str] = None
    object_id: Optional[int] = None
    action: str = Field(..., description="The action for the audit is required")
    before: Optional[dict[str, Any]]= None
    after: Optional[dict[str, Any]]= None

    
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]  = None
    
    class Config:
        orm_mode = True

class AuditSimple(BaseModel):
    #id
    id: Optional[int] = None
    
    #user
    user_id: int
    user_email: str = Field(..., description="The user for the audit is required")
    token: str = Field(..., description="The token for the audit is required")
      
    #audit
    date: datetime = Field(..., description="The date and time for the audit is required")
    feature: str = Field(..., description="The feature for the audit is required")
    model: Optional[str] = None
    object_id: Optional[int] = None
    action: str = Field(..., description="The action for the audit is required")
    
    #service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]  = None
    
    class Config:
        orm_mode = True     
        
class AuditWithDetail(Audit):
    pass

class AuditSimpleWithDetail(AuditSimple):
    pass