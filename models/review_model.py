# ---------- Pydantic Schemas ----------
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SACCOReview(BaseModel):
    #user
    user_id: int =  Field(..., ge=1, description="The review user must be greater or equal to 1")
    
    #review
    review_action: int =  Field(..., ge=1, le=2, description="Review action must be between 1 or 2")
    comments: Optional[str]
    attachment_id: Optional[int]
    content: Optional[str]
            
    class Config:
        orm_mode = True