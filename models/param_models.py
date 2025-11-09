from typing import List, Optional
from pydantic import BaseModel
from models.attachment_model import Attachment
from models.configuration_model import SACCOConfiguration
from models.member_model import Member
from models.transaction_model import Transaction, TransactionWithPenalty


class ParamMonthlyPosting(BaseModel):
    member: Member
    config: SACCOConfiguration
    loan: Optional[Transaction] = None
    totalSavings: float
    totalLoanPaymentsAmount: float
    totalLoanPaymentsNo: float
    totalPenaltiesAmount: float
    penalties: Optional[List[TransactionWithPenalty]] = None
    latePostingStartDay: int

    class Config:
        orm_mode = True


class ParamSummary(BaseModel):
    id: int
    name: str
    amount: float

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
    period: str
    amount: float

    class Config:
        orm_mode = True


class ParamGroupSummary(BaseModel):
    summary: List[ParamSummary]
    members: List[ParamMemberSummary]

    class Config:
        orm_mode = True


class ParamAttendanceSimple(BaseModel):
    user: str
    type: str
    typeId: Optional[int] = None
    penalty: float


class ParamAttachmentDetail(BaseModel):
    attachment: Attachment
    attendance: Optional[List[ParamAttendanceSimple]] = None

    class Config:
        orm_mode = True


class ParamPeriodSummary(BaseModel):
    id: int
    name: str
    year: int
    month: int
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
