from datetime import date, datetime
from typing import List, Optional, Any
from pydantic import BaseModel
from apps.lwsc.models.attachment_model import Attachment
from apps.lwsc.models.complaint_department_model import ComplaintDepartmentItem
from apps.lwsc.models.complaint_model import ComplaintWithDetail
from apps.lwsc.models.customer_category_model import Category
from apps.lwsc.models.configuration_model import AppConfiguration
from apps.lwsc.models.customer_model import Customer
from apps.lwsc.models.district_model import District, DistrictSimple
from apps.lwsc.models.meter_reading_model import MeterReading
from apps.lwsc.models.user_model import User, UserWithDetail, UserWithFullDetail
from apps.lwsc.models.walkroute_model import WalkRoute, WalkRouteWithSimpleDetail

class ParamComplaintReview(BaseModel):
    complaint: Optional[ComplaintWithDetail] = None
    departments: Optional[List[ComplaintDepartmentItem]] = []

    class Config:
        orm_mode = True
        
class ParamUploadTaskResult(BaseModel):
    succeeded: bool
    approved: bool
    message: str
    imageUrl: Optional[str] = ''
    meterreading: MeterReading

    class Config:
        orm_mode = True


class ParamUserEdit(BaseModel):
    user: Optional[UserWithFullDetail] = None
    districts: Optional[List[DistrictSimple]] = []
    routes: Optional[List[WalkRouteWithSimpleDetail]] = []

    class Config:
        orm_mode = True


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
    cat_id: Optional[int] = None
    district_id: int
    items: Optional[list[dict[str, Any]]] = []

    class Config:
        orm_mode = True

class ParamMetersImport(BaseModel):
    user_id: int
    items: Optional[list[dict[str, Any]]] = []

    class Config:
        orm_mode = True


class ParamReadingInitialize(BaseModel):
    user_id: int
    period_date: date

    class Config:
        orm_mode = True


class ParamMeterReaderProgress(BaseModel):
    # reader
    user_id: int
    code: Optional[str] = None
    name: str
    email: str
    district_name: Optional[str] = None

    # what the reader is responsible for
    routes_assigned: int
    customers_assigned: int

    # what has happened in the period
    readings_total: int
    readings_awaiting: int
    readings_submitted: int
    readings_approved: int

    # progress
    progress_percent: float
    last_read_date: Optional[datetime] = None

    class Config:
        orm_mode = True


class ParamDistrictProgress(BaseModel):
    # district
    district_id: int
    name: str
    code: str

    # what the district is made up of
    routes: int
    readers_assigned: int
    customers: int

    # what has happened in the period
    readings_total: int
    readings_awaiting: int
    readings_submitted: int
    readings_approved: int

    # progress
    progress_percent: float
    last_read_date: Optional[datetime] = None

    class Config:
        orm_mode = True