# ---------- Pydantic Schemas ----------
from pydantic import BaseModel, Field


class MobileParam(BaseModel):

    mobile: str = Field(..., min_length=3, max_length=15, description="Mobile phone must be between 3 and 15 characters")
    class Config:
        orm_mode = True
        
class AuthParam(BaseModel):

    mobile: str = Field(..., min_length=3, max_length=15, description="Mobile phone must be between 3 and 15 characters")
    code: str =  Field(..., min_length=6, max_length=6, description="The code must be 6-characters")
    class Config:
        orm_mode = True

class ItemReviewParam(BaseModel):
    id: int = Field(..., ge=1, description="The id must be greater than or equal to 1")
    action: str = Field(..., min_length=3, description="Action must be between 3 and 15 characters")
    class Config:
        orm_mode = True
        
class TransactionReviewParam(BaseModel):
    id: int = Field(..., ge=1, description="The id must be greater than or equal to 1")
    type: str = Field(..., min_length=3, description="Type must be between 3 and 15 characters")
    amount: str = Field(..., min_length=3, description="Amount must be between 3 and 15 characters")
    action: str = Field(..., min_length=3, description="Action must be between 3 and 15 characters")
    class Config:
        orm_mode = True