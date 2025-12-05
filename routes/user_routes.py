from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from helpers import assist
from models.user_model import User, UserDB, UserSimple, UserWithDetail

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/create", response_model=User)
async def create_user(user: User, db: AsyncSession = Depends(get_db)):
    # Check duplicate email
    result = await db.execute(select(UserDB).where(UserDB.email == user.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400, detail=f"The email '{user.email}' is already registered"
        )

    db_user = UserDB(
        # id
        code=user.code,
        type=user.type,
        # personal details
        fname=user.fname,
        lname=user.lname,
        position=user.position,
        # contact, address
        email=user.email,
        mobile=user.mobile,
        address_physical=user.address_physical,
        address_postal=user.address_postal,
        # account
        role=user.role,
        password=assist.hash_password(user.password),
        # approval
        status_id=user.status_id,
        stage_id=user.stage_id,
        approval_levels=user.approval_levels,
        # service
        created_by=user.email,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create user: f{e}")
    return db_user


@router.get("/id/{user_id}", response_model=UserWithDetail)
async def get_user_id(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserDB)
        # .options(
        #    joinedload(TransactionDB.post),
        #    joinedload(TransactionDB.status),
        #    joinedload(TransactionDB.type),
        #    joinedload(TransactionDB.source),
        #
        # )
        .filter(UserDB.id == user_id)
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(
            status_code=404, detail=f"Unable to find user with specified id '{user_id}'"
        )
    return transaction


@router.get("/email/{user_email}", response_model=List[UserSimple])
async def get_user_email(user_email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserDB)
        # .options(
        #    joinedload(TransactionDB.post),
        #    joinedload(TransactionDB.status),
        #    joinedload(TransactionDB.type),
        #    joinedload(TransactionDB.source),
        #
        # )
        .filter(UserDB.email == user_email)
    )
    users = []

    user = result.scalars().first()
    if user:
        users.append(user)

    return users


@router.get("/list", response_model=List[UserWithDetail])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB))
    return result.scalars().all()
