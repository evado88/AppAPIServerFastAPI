from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel
from apps.lwsc.models.attachment_model import Attachment
from apps.lwsc.models.configuration_model import AppConfiguration


class ParamDetail(BaseModel):
    status_code: int
    detail: str

    class Config:
        orm_mode = True





class ParamMemberSummary(BaseModel):
    id: int
    fname: str
    lname: str
    email: str
    phone: str
    tid1: float
    tid2: float
    tid3: float
    tid4: float
    tid5: float
    tid6: float
    tid7: float
    tid8: float
    tid9: float

    class Config:
        orm_mode = True


class ParamMemberTransaction(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    type: str
    period: date
    amount: float

    class Config:
        orm_mode = True

class ParamExpenseEarningTransaction(BaseModel):
    id: int
    name: str
    user: str
    period: date
    type: str
    amount: float

    class Config:
        orm_mode = True
        


class ParamAttendanceSimple(BaseModel):
    id: int
    user: str
    type: str
    typeId: Optional[int] = None
    penalty: float
    penaltyId: Optional[int] = None


class ParamAttachmentDetail(BaseModel):
    attachment: Attachment
    attendance: Optional[List[ParamAttendanceSimple]] = None

    class Config:
        orm_mode = True


class ParamPeriodSummary(BaseModel):
    id: str
    name: str
    year: int
    month: int
    
    cash_at_bank: float
    late_posting_date_start: date
    late_posting_date_min: date
    late_posting_date_max: date
    
    saving_multiple: float
    shares_multiple: float
    social_min: float

    loan_interest_rate: float
    loan_repayment_rate: float
    loan_saving_ratio: float

    loan_duration: float
    loan_apply_limit: float

    late_posting_rate: float
    missed_meeting_rate: float
    late_meeting_rate: float

    status_id: int
    status: str
    approval_levels: int
    stage_id: int
    stage: str
    sid1: int
    sid2: int
    sid3: int
    sid4: int
    sid5: int
    sid6: int
    sid7: int
    sid8: int

    class Config:
        orm_mode = True


class ParamMonthData(BaseModel):
    id: str
    m1: float
    m2: float
    m3: float
    m4: float
    m5: float
    m6: float
    m7: float
    m8: float
    m9: float
    m10: float
    m11: float
    m12: float

    class Config:
        orm_mode = True


class ParamMemberSharingSummary(BaseModel):
    id: int
    fname: str
    lname: str
    email: str
    phone: str
    bank_name: str
    branch_name: str
    branch_code: str
    bank_account_no: str
    bank_account_name: str
    itotal: float
    stotal: float
    loan_total: float
    loan_interest_total: float
    loan_repayment_total: float
    loan_plus_interest_total: float
    loan_balance: float
    time_value_total: float
    proportional_final_share: float
    payout_balance: float
    tsavings: ParamMonthData
    tsavings: ParamMonthData
    isharing: ParamMonthData

    class Config:
        orm_mode = True


class ParamTotalsSummary(BaseModel):
    total_loan_balance: float
    group_time_value_total: float
    group_proportional_final_share: float
    group_share_total: float
    group_money_growth_total: float
    group_money_growth_percent: float
    group_payout_balance: float
    t1: ParamMonthData
    t3: ParamMonthData
    t5: ParamMonthData
    r1: ParamMonthData
    r2: ParamMonthData
    r3: ParamMonthData

    class Config:
        orm_mode = True


class ParamInterestSharingSummary(BaseModel):
    totals: ParamTotalsSummary
    members: List[ParamMemberSharingSummary]

    class Config:
        orm_mode = True
