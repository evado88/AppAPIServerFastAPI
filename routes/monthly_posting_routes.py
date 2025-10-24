from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy import func
from database import get_db
from models.configuration_model import SACCOConfigurationDB
from models.monthly_post_model import (
    MonthlyPosting,
    MonthlyPostingDB,
    MonthlyPostingWithDetail,
)
from models.param_models import ParamMonthlyPosting
from models.review_model import SACCOReview
from models.transaction_model import Transaction, TransactionDB
from models.user_model import UserDB
from models.status_types_model import StatusTypeDB

import helpers.assist as assist

router = APIRouter(prefix="/monthly-posting", tags=["MonthlyPosting"])


@router.post("/create", response_model=MonthlyPosting)
async def post_posting(posting: MonthlyPosting, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == posting.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id {posting.user_id} does not exist"
        )

    # check if posting has been made this month
    start_date = assist.get_first_month_day(posting.date)
    end_date = assist.get_last_month_day(posting.date)

    result = await db.execute(
        select(MonthlyPostingDB).filter(
            MonthlyPostingDB.date.between(start_date, end_date)
        )
    )

    monthPosting = result.scalars().first()

    if monthPosting:
        raise HTTPException(
            status_code=400,
            detail=f"You have already made a posting for {posting.date.strftime('%B %Y')}",
        )

    db_tran = MonthlyPostingDB(
        # user
        user_id=posting.user_id,
        # period
        period_id=posting.period_id,
        # posting
        date=posting.date,
        saving=posting.saving,
        shares=posting.shares,
        social=posting.social,
        penalty=posting.penalty,
        loan_interest=posting.loan_interest,
        loan_month_repayment=posting.loan_month_repayment,
        loan_application=posting.loan_application,
        comments=posting.comments,
        # validation
        contribution_total=posting.contribution_total,
        deposit_total=posting.deposit_total,
        # approval
        status_id=posting.status_id,
        stage_id=posting.stage_id,
        approval_levels=posting.approval_levels,
        # service
        created_by=posting.created_by,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to create monthly posting: {e}"
        )
    return db_tran


@router.put("/review-update/{post_id}", response_model=MonthlyPostingWithDetail)
async def review_posting(
    post_id: int, review: SACCOReview, db: AsyncSession = Depends(get_db)
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == review.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{review.user_id}' does not exist",
        )

    # check posting exists
    result = await db.execute(
        select(MonthlyPostingDB).where(MonthlyPostingDB.id == post_id)
    )
    posting = result.scalar_one_or_none()

    if not posting:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find monthly posting with id '{post_id}' not found",
        )

    if review.review_action == 1:
        # reject
        posting.status_id = 5
    else:
        posting.status_id = 4

    posting.updated_by = user.email

    try:
        await db.commit()
        await db.refresh(posting)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update monthly posting {e}"
        )
    return posting


@router.get("/list", response_model=List[MonthlyPostingWithDetail])
async def list_postings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonthlyPostingDB)
        # .options(
        #    joinedload(MonthlyPostingDB.status),
        # )
    )
    postings = result.scalars().all()
    return postings


@router.get("/status/{status_id}", response_model=List[MonthlyPostingWithDetail])
async def list_status_postings(status_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonthlyPostingDB)
        # .options(
        #    joinedload(MonthlyPostingDB.status),
        # )
        .filter(MonthlyPostingDB.status_id == status_id)
    )
    postings = result.scalars().all()
    return postings


@router.get("/id/{posting_id}", response_model=MonthlyPostingWithDetail)
async def get_posting(posting_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonthlyPostingDB)
        # .options(
        #    joinedload(MonthlyPostingDB.status),
        # )
        .filter(MonthlyPostingDB.id == posting_id)
    )
    posting = result.scalars().first()
    if not posting:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find monthly posting with id '{posting_id}'",
        )
    return posting


@router.get("/param/{user_id}", response_model=ParamMonthlyPosting)
async def get_postomng_param(user_id: int, db: AsyncSession = Depends(get_db)):

    # check user exists
    result = await db.execute(select(UserDB).filter(UserDB.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=401, detail=f"The specified user '{user_id}' does not exist"
        )

    result = await db.execute(
        select(SACCOConfigurationDB).filter(SACCOConfigurationDB.id == 1)
    )
    config = result.scalars().first()
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to load param: Configuration with id '{1}' not found",
        )

    # get savings
    stmt = select(func.sum(TransactionDB.amount)).filter(
        TransactionDB.user_id == user_id,
        TransactionDB.type_id == assist.TRANSACTION_SAVINGS,
        TransactionDB.status_id == assist.STATUS_APPROVED,
    )

    result = await db.execute(stmt)

    totalSavings = result.scalar() or 0.0

    # get loan that is open
    result = await db.execute(
        select(TransactionDB).filter(
            TransactionDB.user_id == user_id,
            TransactionDB.type_id == assist.TRANSACTION_LOAN,
            TransactionDB.status_id == assist.STATUS_APPROVED,
            TransactionDB.state_id == assist.STATE_OPEN,
        )
    )

    loan = result.scalars().first()
    totalLoanPaymentsAmount = 0.0
    totalLoanPaymentsNo = 0

    # check if there is a loan
    if loan:
        # there is loan, check payments made against loan
        stmt = select(func.sum(TransactionDB.amount)).filter(
            TransactionDB.user_id == user_id,
            TransactionDB.type_id == assist.TRANSACTION_LOAN_PAYMENT,
            TransactionDB.status_id == assist.STATUS_APPROVED,
            TransactionDB.parent_id == loan.id,
        )

        result = await db.execute(stmt)

        totalLoanPaymentsAmount = result.scalar() or 0.0

        # there is loan, check payments made against loan
        stmt = select(func.count(TransactionDB.amount)).filter(
            TransactionDB.user_id == user_id,
            TransactionDB.type_id == assist.TRANSACTION_LOAN_PAYMENT,
            TransactionDB.status_id == assist.STATUS_APPROVED,
            TransactionDB.parent_id == loan.id,
        )

        result = await db.execute(stmt)

        totalLoanPaymentsNo = result.scalar() or 0.0

    # penelties
    result = await db.execute(
        select(TransactionDB).filter(
            TransactionDB.user_id == user_id,
            TransactionDB.type_id == assist.TRANSACTION_PENALTY_CHARGED,
            TransactionDB.status_id == assist.STATUS_APPROVED,
            TransactionDB.state_id == assist.STATE_OPEN,
        )
    )

    penalties = result.scalars().all()
    totalPenalties = sum(item.amount for item in penalties)

    # postingDate = assist.get_current_date()

    # latePostingdate = datetime(postingDate.year, postingDate.month, config.late_posting_date_start.day)

    # postingStatus = 'Late' if postingDate >= latePostingdate else 'Normal'
    # return

    param = {
        "config": config,
        "totalSavings": totalSavings,
        "loan": loan,
        "totalLoanPaymentsAmount": totalLoanPaymentsAmount,
        "totalLoanPaymentsNo": totalLoanPaymentsNo,
        "totalPenaltiesAmount": totalPenalties,
        "penalties": penalties,
        "latePostingStartDay": config.late_posting_date_start.day,
    }

    return param
