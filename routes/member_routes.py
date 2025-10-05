from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.member_model import Member, MemberDB, MemberWithDetail
from models.user_model import User, UserDB

router = APIRouter(prefix="/members", tags=["Members"])


@router.post("/register", response_model=Member)
async def register_member(member: Member, db: AsyncSession = Depends(get_db)):
    # Check duplicate email
    result = await db.execute(select(UserDB).where(UserDB.email == member.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = MemberDB(
        #personal details
        fname=member.fname,
        lname=member.lname,
        mobile1=member.mobile1,
        mobile2=member.mobile2,
        id_type=member.id_type,
        id_no = member.id_no,
        email=member.email,
        dob=member.dob,
        #guarantor
        guar_fname = member.guar_fname,
        guar_lname =  member.guar_lname,
        guar_mobile =  member.guar_mobile,
        guar_email =  member.guar_email,
        #banking
        bank_name = member.bank_name,
        bank_branch = member.bank_branch,
        bank_acc_name = member.bank_acc_name,
        bank_acc_no = member.bank_acc_no,
        #approval
        status_id = member.status_id,
        stage_id = member.stage_id,
        approval_levels = member.approval_levels,


        #service
        created_by = member.email,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to register member: f{e}")
    return db_user


@router.get("/{member_id}", response_model=MemberWithDetail)
async def get_member(member_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MemberDB)
        #.options(
        #    joinedload(TransactionDB.post),
        #    joinedload(TransactionDB.status),
        #    joinedload(TransactionDB.type),
        #    joinedload(TransactionDB.source),
        #
        #)
        .filter(MemberDB.id == member_id)
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(status_code=404, detail=f"Member with id '{member_id}' not found")
    return transaction

@router.get("/", response_model=List[MemberWithDetail])
async def list_members(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MemberDB))
    return result.scalars().all()

