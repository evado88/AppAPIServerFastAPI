from typing import List, Optional
from pydantic import BaseModel
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