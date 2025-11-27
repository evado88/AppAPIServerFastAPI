from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from jose import JWTError, jwt
from database import get_db
from models.member_model import MemberDB
from models.user_model import User, UserDB
import helpers.assist as assist
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/data", tags=["Data"])


class ExportParam(BaseModel):

    filename: str = Field(..., min_length=3, description="Filename must be at least 3 characters")
    jsonArray: list[dict]
    
    class Config:
        orm_mode = True
        
@router.post("/export-excel")
def export_excel(param: ExportParam):
    # Convert to DataFrame
    df = pd.DataFrame(param.jsonArray)

    # Create Excel in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={param.filename}.xlsx"
        }
    )