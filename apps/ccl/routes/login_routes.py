from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.login_model import Login, LoginDB

router = APIRouter(prefix="/logins", tags=["Logins"])


@router.post("/create", response_model=Login)
async def create_status(login: Login, db: AsyncSession = Depends(get_ccl_db)):
    
    db_user = LoginDB(
        #personal details
        username=login.username,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create login: f{e}")
    return db_user


@router.get("/list", response_model=List[Login])
async def list_logins(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(LoginDB))
    return result.scalars().all()

