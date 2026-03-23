from datetime import date, datetime
from typing import List, Optional, Any
from pydantic import BaseModel
from apps.lwsc.models.attachment_model import Attachment
from apps.lwsc.models.configuration_model import AppConfiguration


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