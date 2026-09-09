from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from apps.lwsc.lwscdb import Base
from datetime import datetime

from apps.lwsc.models.review_stages_model import ReviewStage, ReviewStageItem
from apps.lwsc.models.status_types_model import StatusType, StatusTypeItem
from apps.lwsc.models.district_model import District, DistrictItem, DistrictSimple
from apps.lwsc.models.user_model import User, UserSimple
from apps.lwsc.models.walkroute_model import WalkRouteWithDetail, WalkRouteWithSimpleDetail


# ---------- SQLAlchemy Models ----------
class MeterReaderWalkRouteDB(Base):
    __tablename__ = "meter_reader_routes"

    # id
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # route
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    
    # service columns
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    created_by = Column(String, nullable=True, default="System")
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now, nullable=True)
    updated_by = Column(String, nullable=True)

    # relationships
    user = relationship("UserDB", back_populates="readerroutes", lazy="raise")
    route = relationship("WalkRouteDB", back_populates="readerroutes", lazy="raise")

# ---------- Pydantic Schemas ----------
class MeterReaderWalkRoute(BaseModel):
    # id
    id: Optional[int] = None
    
    # user
    user_id: int
    
    # route
    route_id: int
    
    # service columns
    created_at: Optional[datetime] = None
    created_by: Optional[str]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str]

    class Config:
        orm_mode = True
    

class MeterReaderWalkRouteWithDetail(MeterReaderWalkRoute):
    user: UserSimple
    route: WalkRouteWithSimpleDetail

