from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.user_model import User, UserDB

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=User)
async def create_user(user: User, db: AsyncSession = Depends(get_db)):
    # Check duplicate email
    result = await db.execute(select(UserDB).where(UserDB.email == user.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = UserDB(
        #personal details
        role = user.role,
        fname=user.fname,
        lname=user.lname,
        mobile1=user.mobile1,
        mobile2=user.mobile2,
        id_type=user.id_type,
        id_no = user.id_no,
        email=user.email,
        dob=user.dob,
        #guarantor
        guar_fname = user.guar_fname,
        guar_lname =  user.guar_lname,
        guar_mobile =  user.guar_mobile,
        guar_email =  user.guar_email,
        #banking
        bank_name = user.bank_name,
        bank_branch = user.bank_branch,
        bank_acc_name = user.bank_acc_name,
        bank_acc_no = user.bank_acc_no,
        #account
        password = user.password,
        #service columns
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not register user: f{e}")
    return db_user


@router.get("/", response_model=List[User])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB))
    return result.scalars().all()

