from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from jose import JWTError, jwt
from apps.osawe.osawedb import get_osawe_db
from apps.osawe.models.member_model import MemberDB
from apps.osawe.models.user_model import User, UserDB
import helpers.assist as assist

router = APIRouter(prefix="/sensor", tags=["Sensor"])

db: List["Asset"] = []

# -----------------------
# Pydantic model
# -----------------------
class Asset(BaseModel):
    asset_name: str
    motion: bool
    temperature: float
    asset_uid: str
    sos_mode: bool


# -----------------------
# POST endpoint
# -----------------------
@router.post("/assets", response_model=Asset)
def create_asset(asset: Asset):
    db.append(asset)
    return asset

# -----------------------
# GET endpoint
# -----------------------
@router.get("/assets", response_model=List[Asset])
def list_assets():
    return db