from pydantic import BaseModel
from models.configuration_model import SACCOConfiguration


class ParamMonthlyPosting(BaseModel):
    config: SACCOConfiguration
    loan: float
    totalSavings: float
