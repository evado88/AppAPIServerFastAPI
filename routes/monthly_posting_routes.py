from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, joinedload
from typing import List

from database import get_db
from models.monthly_post_model import MonthlyPosting, MonthlyPostingDB, MonthlyPostingWithDetail
from models.user_model import UserDB
from models.status_types_model import StatusTypeDB

router = APIRouter(prefix="/monthly-posting", tags=["MonthlyPosting"])


@router.post("/", response_model=MonthlyPosting)
async def post_transaction(posting: MonthlyPosting, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == posting.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id {posting.user_id} does not exist"
        )

    db_tran = MonthlyPostingDB(
        # user
        user_id = posting.user_id,
        # posting
        date = posting.date,
        saving = posting.saving,
        shares = posting.shares,
        social = posting.social,
        penalty = posting.penalty,
        
        loan_interest = posting.loan_interest,
        loan_amount_payment = posting.loan_amount_payment,
        loan_month_repayment = posting.loan_month_repayment,
        
        loan_application = posting.loan_application,
        
        comments = posting.comments,

        # approval
        status_id=posting.status_id,
        stage_id = posting.stage_id,
        approval_levels = posting.approval_levels,
        
        # service
        created_by=posting.created_by,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Unable to create monthly posting")
    return db_tran


@router.get("/", response_model=List[MonthlyPostingWithDetail])
async def list_postings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonthlyPostingDB)
        #.options(
        #    joinedload(MonthlyPostingDB.status),
        #)
    )
    posting = result.scalars().all()
    return posting


@router.get("/{posting_id}", response_model=MonthlyPostingWithDetail)
async def get_posting(posting_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonthlyPostingDB)
        #.options(
        #    joinedload(MonthlyPostingDB.status),
        #)
        .filter(MonthlyPostingDB.id == posting_id)
    )
    posting = result.scalars().first()
    if not posting:
        raise HTTPException(status_code=404, detail=f"Unable to find monthly posting with id '{posting_id}'")
    return posting
