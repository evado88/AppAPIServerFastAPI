from datetime import date, datetime
from typing import List, Optional, Any
from pydantic import BaseModel
from apps.lwsc.models.attachment_model import Attachment
from apps.lwsc.models.category_model import Category
from apps.lwsc.models.configuration_model import AppConfiguration
from apps.lwsc.models.customer_model import Customer
from apps.lwsc.models.district_model import District
from apps.lwsc.models.walkroute_model import WalkRoute


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