from typing import List, Optional
from pydantic import BaseModel
from models.attachment_model import Attachment
from models.configuration_model import SACCOConfiguration
from models.transaction_model import Transaction, TransactionWithPenalty


class ParamMonthlyPosting(BaseModel):
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

class MemberSummary(BaseModel):
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

class ParamGroupSummary(BaseModel):
    summary: List[ParamSummary]
    members: List[MemberSummary]

    class Config:
        orm_mode = True


class AttendanceSimple(BaseModel):
    user: str 
    type: str 
    
class ParamAttachmentDetail(BaseModel):
    attachment: Attachment
    attendance: List[AttendanceSimple]

    class Config:
        orm_mode = True