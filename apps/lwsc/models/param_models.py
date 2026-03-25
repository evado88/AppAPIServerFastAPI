from datetime import date, datetime
from typing import List, Optional, Any
from pydantic import BaseModel
from apps.lwsc.models.attachment_model import Attachment
from apps.lwsc.models.category_model import Category
from apps.lwsc.models.configuration_model import AppConfiguration
from apps.lwsc.models.customer_model import Customer
from apps.lwsc.models.district_model import District
from apps.lwsc.models.walkroute_model import WalkRoute


class ParamDashboardStatistic(BaseModel):
    name: str
    value: float
    color: str

    class Config:
        orm_mode = True

class ParamChartItem(BaseModel):
    type: str
    id: Optional[int] = None
    name: str
    value: float

    class Config:
        orm_mode = True

class ParamChartSeries(BaseModel):
    items: Optional[List[ParamChartItem]] = []

    class Config:
        orm_mode = True

class ParamChartData(BaseModel):
    data: Optional[List[ParamChartSeries]] = []

    class Config:
        orm_mode = True

class ParamDashboardYearSummary(BaseModel):
    statistics: Optional[List[ParamDashboardStatistic]] = []
    months: Optional[List[ParamChartItem]] = []
    districts: Optional[List[ParamChartItem]] = []
    categories: Optional[List[ParamChartItem]] = []
    categoriesCount: Optional[List[ParamChartItem]] = []
    
    class Config:
        orm_mode = True
             
class ParamCustomer(BaseModel):
    customer: Customer
    districts: Optional[List[District]] = []
    routes: Optional[List[WalkRoute]] = []
    categories: Optional[List[Category]] = []

    class Config:
        orm_mode = True
        
class ParamDetail(BaseModel):
    status_code: int
    detail: str

    class Config:
        orm_mode = True


class ParamAttachmentDetail(BaseModel):
    attachment: Attachment
    items: Optional[list[dict[str, Any]]] = []

    class Config:
        orm_mode = True
        
class ParamCustomerImport(BaseModel):
    user_id: int
    cat_id: int
    district_id: int
    route_id: int
    items: Optional[list[dict[str, Any]]] = []

    class Config:
        orm_mode = True