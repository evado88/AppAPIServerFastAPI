from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from jose import JWTError, jwt
from database import get_db
from models.member_model import MemberDB
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
        #check if this person has registered as a member
        result = await db.execute(select(MemberDB).where(MemberDB.email == form_data.username))
        member = result.scalars().first()
        
        if member and member.status_id == assist.STATUS_SUBMITTED:
            #registered as a member
            raise HTTPException(
                status_code=401, detail=f"Your account is not yet active. You will be notifed once approved"
            )
        else:
            #not registered
            raise HTTPException(
                status_code=401, detail=f"The specified username or password is incorrect"
            )
            
    if not assist.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=401, detail=f"The specified username or password is incorrect"
        )

    to_encode = {
        "sub": user.email,
        "userid": user.id,
        "name": f"{user.fname} {user.lname}",
        "role": user.role,
        "mobile": user.mobile,
        "exp":  datetime.now(timezone.utc) + timedelta( minutes=30),
    }
    token = jwt.encode(to_encode, assist.SECRET_KEY, algorithm=assist.ALGORITHM)

    return {"access_token": token, "token_type": "bearer"}
