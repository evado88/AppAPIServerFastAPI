from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from jose import JWTError, jwt
from database import get_db
from models.user_model import User, UserDB
import helpers.assist as assist

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.email == form_data.username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=401, detail=f"The specified username or password is incorrect"
        )

    if not user.password == assist.encode_sha256(form_data.password):
        raise HTTPException(
            status_code=401, detail=f"The specified username or password is incorrect"
        )

    to_encode = {
        "sub": user.email,
        "name": f"{user.fname} {user.lname}",
        "role": user.role,
        "exp":  datetime.now(timezone.utc) + timedelta( minutes=0.2),
    }
    token = jwt.encode(to_encode, assist.SECRET_KEY, algorithm=assist.ALGORITHM)

    return {"access_token": token, "token_type": "bearer"}
