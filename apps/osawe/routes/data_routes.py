from datetime import datetime, timedelta, timezone, date
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from jose import JWTError, jwt
from apps.osawe.osawedb import get_osawe_db
from apps.osawe.models.member_model import MemberDB
from apps.osawe.models.user_model import User, UserDB
import helpers.assist as assist
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/data", tags=["Data"])


class ExportParam(BaseModel):

    filename: str = Field(..., min_length=3, description="Filename must be at least 3 characters")
    jsonArray: list[dict]
    columns: list[dict]
    
    class Config:
        orm_mode = True
        

def excel_date(value):
    """
    Convert ISO 8601 string or datetime/date object into Excel-friendly string,
    using Africa/Lusaka timezone.
    Returns 'YYYY-MM-DD' if time is 00:00:00, otherwise 'YYYY-MM-DD HH:MM:SS'.
    """
    if value is None:
        return None

    # Parse string if necessary
    if isinstance(value, str):
        value = value.strip()
        try:
            dt = datetime.fromisoformat(value)  # may be offset-aware
        except ValueError:
            return value  # return original string if parsing fails
    elif isinstance(value, date) and not isinstance(value, datetime):
        dt = datetime.combine(value, datetime.min.time())
    elif isinstance(value, datetime):
        dt = value
    else:
        return value

    # Convert to Africa/Lusaka timezone
    lusaka_tz = ZoneInfo("Africa/Lusaka")

    if dt.tzinfo is None:
        # naive → assume UTC
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(lusaka_tz)

    # Format for Excel
    if dt.time() == datetime.min.time():
        return dt.date().isoformat()  # YYYY-MM-DD
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")  # YYYY-MM-DD HH:MM:SS


def excel_serial(value):
    """
    Convert ISO 8601 string or datetime/date object into Excel serial number,
    converting all times to Africa/Lusaka timezone.
    """
    if value is None:
        return None

    # Parse string if necessary
    if isinstance(value, str):
        value = value.strip()
        try:
            dt = datetime.fromisoformat(value)  # can be offset-aware
        except ValueError:
            return None
    elif isinstance(value, date) and not isinstance(value, datetime):
        dt = datetime.combine(value, datetime.min.time())
    elif isinstance(value, datetime):
        dt = value
    else:
        return None

    # Convert to Africa/Lusaka timezone
    lusaka_tz = ZoneInfo(assist.CURRENT_TIME_ZONE)

    if dt.tzinfo is None:
        # naive → assume UTC
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(lusaka_tz).replace(tzinfo=None)  # make naive in Lusaka

    # Excel base date
    excel_start = datetime(1899, 12, 30)  # Excel day 1 = 1900-01-01
    delta = dt - excel_start
    return delta.days + delta.seconds / 86400  # include fraction of day

def get_nested_value(obj, path):
    keys = path.split(".")
    for key in keys:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
        if obj is None:
            return None
    return obj
        
@router.post("/export-excel")
def export_excel(param: ExportParam):
    #process data
    result = []

    for row in param.jsonArray:
        item = {}
        for col in param.columns:
            caption = col["caption"]
            field = col["dataField"]
            value = get_nested_value(row, field)

            if col.get("dataType") == "date":
                #add option in config to handle wether user wants serial or string
                value = excel_date(value)

            item[caption] = value
        result.append(item)
        
    # Convert to DataFrame
    df = pd.DataFrame(result)

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