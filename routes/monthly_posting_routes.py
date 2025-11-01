from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
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
import os
import uuid
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
            MonthlyPostingDB.date.between(start_date, end_date),
            MonthlyPostingDB.user_id == posting.user_id,
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
        late_post_penalty=posting.late_post_penalty,
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


@router.post("/upload-pop/{post_id}", response_model=MonthlyPosting)
async def upload_file(
    post_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):

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

    try:
        # ensure folders exist
        current = assist.get_current_date()
        dir = f"{assist.UPLOAD_DIR}/{current.year}/{current.month}"

        os.makedirs(dir, exist_ok=True)

        # Validate filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Generate unique name
        fileDetail = os.path.splitext(file.filename)
        noextensionfile = fileDetail[0]
        ext = fileDetail[1]

        unique_name = f"{noextensionfile}_{uuid.uuid4()}{ext}"
        file_path = os.path.join(dir, unique_name)

        # Save file safely
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        # update pop file
        posting.pop_filename = f"{current.year}/{current.month}/{unique_name}"
        posting.pop_filesize = len(contents)
        posting.pop_filetype = file.content_type

        await db.commit()
        await db.refresh(posting)

        # rerturn response
        return posting

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


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

    if posting.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The monthly posting with id '{post_id}' has already been approved",
        )

    posting.updated_by = user.email

    if posting.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        posting.review1_at = assist.get_current_date(False)
        posting.review1_by = user.email
        posting.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            posting.status_id = assist.STATUS_REJECTED
        else:
            # approve

            posting.guarantor_required = review.require_guarantor_approval

            # check number of approval levels
            if posting.approval_levels == 1:
                # one level, no furthur stage approvers

                if review.require_guarantor_approval == assist.RESPONSE_NO:
                    # no guarantor approval
                    posting.stage_id = assist.APPROVAL_STAGE_POP_UPLOAD
                else:
                    # require guarantor approval
                    posting.stage_id = assist.APPROVAL_STAGE_GUARANTOR

            elif posting.approval_levels == 2 or posting.approval_levels == 3:
                # two or three levels, move to primary

                posting.stage_id = assist.APPROVAL_STAGE_PRIMARY

    elif posting.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage

        posting.review2_at = assist.get_current_date(False)
        posting.review2_by = user.email
        posting.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            posting.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if posting.approval_levels == 2:
                # two levels, no furthur stage approvers

                if posting.guarantor_required == assist.RESPONSE_NO:
                    # no guarantor approval
                    posting.stage_id = assist.APPROVAL_STAGE_POP_UPLOAD
                else:
                    # require guarantor approval
                    posting.stage_id = assist.APPROVAL_STAGE_GUARANTOR

            elif posting.approval_levels == 3:
                # three levels, move to secondary
                posting.stage_id = assist.APPROVAL_STAGE_SECONDARY

    elif posting.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage

        posting.review3_at = assist.get_current_date(False)
        posting.review3_by = user.email
        posting.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            posting.status_id = assist.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage

            if posting.guarantor_required == assist.RESPONSE_NO:
                # no guarantor approval
                posting.stage_id = assist.APPROVAL_STAGE_POP_UPLOAD
            else:
                # require guarantor approval
                posting.stage_id = assist.APPROVAL_STAGE_GUARANTOR

    elif posting.stage_id == assist.APPROVAL_STAGE_GUARANTOR:
        # guarantor stage

        posting.guarantor_at = assist.get_current_date(False)
        posting.guarantor_by = user.email
        posting.guarantor_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            posting.status_id = assist.STATUS_REJECTED
        else:
            # approve

            posting.stage_id = assist.APPROVAL_STAGE_POP_UPLOAD

    elif posting.stage_id == assist.APPROVAL_STAGE_POP_UPLOAD:
        # pop upload

        posting.stage_id = assist.APPROVAL_STAGE_POP_APPROVAL
        posting.pop_comments = review.comments

    elif posting.stage_id == assist.APPROVAL_STAGE_POP_APPROVAL:
        # move to approved and post transactions
        result = await db.execute(
            select(SACCOConfigurationDB).filter(SACCOConfigurationDB.id == 1)
        )

        config = result.scalars().first()
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to approve monthly posting. Configuration with id '{1}' not found",
            )

        posting.pop_review_at = assist.get_current_date(False)
        posting.pop_review_by = user.email
        posting.pop_review_comments = review.comments

        posting.status_id = assist.STATUS_APPROVED
        posting.stage_id = assist.APPROVAL_STAGE_APPROVED

        # add transactions to database
        items = [
            {
                "type": assist.TRANSACTION_SAVINGS,
                "amount": posting.saving,
                "term": None,
                "interest": None,
                "penaltyType": None,
            },
            {
                "type": assist.TRANSACTION_SHARE,
                "amount": posting.shares,
                "term": None,
                "interest": None,
                "penaltyType": None,
            },
            {
                "type": assist.TRANSACTION_SOCIAL_FUND,
                "amount": posting.social,
                "term": None,
                "interest": None,
                "penaltyType": None,
            },
        ]

        if posting.late_post_penalty != 0:

            items.append(
                {
                    "type": assist.TRANSACTION_PENALTY_CHARGED,
                    "amount": posting.late_post_penalty,
                    "term": None,
                    "interest": None,
                    "penaltyType": assist.PENALTY_LATE_POSTING,
                }
            )
            items.append(
                {
                    "type": assist.TRANSACTION_PENALTY_PAID,
                    "amount": posting.late_post_penalty,
                    "term": None,
                    "interest": None,
                    "penaltyType": assist.PENALTY_LATE_POSTING,
                }
            )

        if posting.loan_application != 0:
            items.append(
                {
                    "type": assist.TRANSACTION_LOAN,
                    "amount": posting.loan_application,
                    "term": config.loan_duration,
                    "interest": config.loan_interest_rate,
                    "penaltyType": assist.PENALTY_LATE_POSTING,
                }
            )

        for item in items:
            db_tran = TransactionDB(
                # id
                type_id=item["type"],
                penalty_type_id=item["penaltyType"],
                # user
                user_id=posting.user_id,
                post_id=posting.id,
                # transaction
                date=assist.get_current_date(False),
                source_id=1,
                amount=item["amount"],
                comments=posting.period.period_name,
                # reference = tran.reference,
                # loan
                term_months=item["term"],
                interest_rate=item["interest"],
                # loan payment transaction id
                # parent_id = tran.parent_id,
                # approval
                status_id=assist.STATUS_APPROVED,
                state_id=assist.STATE_CLOSED,
                stage_id=assist.APPROVAL_STAGE_APPROVED,
                approval_levels=posting.approval_levels,
                # service
                created_by=posting.created_by,
            )
            db.add(db_tran)

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


@router.get("/user/{userId}", response_model=List[MonthlyPostingWithDetail])
async def list_user_postings(userId: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonthlyPostingDB)
        # .options(
        #    joinedload(MonthlyPostingDB.status),
        # )
        .filter(MonthlyPostingDB.user_id == userId)
    )
    postings = result.scalars().all()
    return postings


@router.get(
    "/guarantor-approvals/{userId}", response_model=List[MonthlyPostingWithDetail]
)
async def list_user_postings(userId: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonthlyPostingDB)
        # .options(
        #    joinedload(MonthlyPostingDB.status),
        # )
        .filter(
            MonthlyPostingDB.guarantor_required == assist.RESPONSE_YES,
            MonthlyPostingDB.guarantor_user_id == userId,
        )
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


@router.get("/period/{period_id}", response_model=List[MonthlyPostingWithDetail])
async def list_period_postings(period_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonthlyPostingDB)
        # .options(
        #    joinedload(MonthlyPostingDB.status),
        # )
        .filter(MonthlyPostingDB.period_id == period_id)
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


@router.put("/update/{id}", response_model=MonthlyPosting)
async def update_configuration(
    id: int, posting_update: MonthlyPosting, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MonthlyPostingDB).where(MonthlyPostingDB.id == id))
    posting = result.scalar_one_or_none()

    if not posting:
        raise HTTPException(
            status_code=404, detail=f"Unable to find monthly posting with id '{id}'"
        )

    # Update fields that are not None
    for key, value in posting_update.dict(exclude_unset=True).items():
        setattr(posting, key, value)

    try:
        await db.commit()
        await db.refresh(posting)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update monthly posting: {e}"
        )
    return posting


@router.get("/param/{user_id}", response_model=ParamMonthlyPosting)
async def get_posting_param(user_id: int, db: AsyncSession = Depends(get_db)):

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
