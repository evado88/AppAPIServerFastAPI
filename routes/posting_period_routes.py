from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy import update
import calendar
from sqlalchemy import func, and_, or_
from database import get_db
from helpers import assist
from models.configuration_model import SACCOConfigurationDB
from models.member_model import MemberDB
from models.monthly_post_model import MonthlyPostingDB, MonthlyPostingWithMemberDetail
from models.param_models import ParamPeriodSummary
from models.posting_period_model import (
    PostingPeriod,
    PostingPeriodDB,
    PostingPeriodWithDetail,
)
from models.review_model import SACCOReview
from models.review_stages_model import ReviewStageDB
from models.status_types_model import StatusTypeDB
from models.user_model import UserDB
import datetime as dt

router = APIRouter(prefix="/posting-periods", tags=["PostingPeriods"])


@router.post("/create", response_model=PostingPeriodWithDetail)
async def create_period(period: PostingPeriod, db: AsyncSession = Depends(get_db)):

    db_user = PostingPeriodDB(
        # personal details
        id=period.id,
        period_name=period.period_name,
        start_date=period.month,
        end_date=period.year,
        # approval
        status_id=period.status_id,
        stage_id=period.stage_id,
        approval_levels=period.approval_levels,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to create posting period: f{e}"
        )
    return db_user


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SACCOConfigurationDB).where(SACCOConfigurationDB.id == 1)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find configuration with id '1' not found",
        )

    # Loop through years 2025 and 2026
    for yearNo in range(2025, 2027):
        # Loop through all months (1–12)
        for monthNo in range(1, 13):

            minDate = dt.datetime(yearNo, monthNo, 1)
            maxDate = dt.datetime(yearNo, monthNo, 21)

            loan_interest_rate = config.loan_interest_rate
            loan_repayment_rate = config.loan_repayment_rate
            loan_duration = config.loan_duration

            # assign interest rates appropriately
            if monthNo == 10:
                # october 7.5%
                loan_interest_rate = 0.075
                loan_repayment_rate = 0.075
                loan_duration = 3
            elif monthNo == 11:
                # november 5%
                loan_interest_rate = 0.05
                loan_repayment_rate = 0.05
                loan_duration = 2
            elif monthNo == 12:
                # december 2.5%
                loan_interest_rate = 0.025
                loan_repayment_rate = 0.025
                loan_duration = 1

            db_status = PostingPeriodDB(
                # personal details
                id=dt.datetime(yearNo, monthNo, 1).strftime("%Y%m"),
                period_name=f"{calendar.month_name[monthNo]} {yearNo}",
                month=monthNo,
                year=yearNo,
                # accounts
                cash_at_bank=0,
                # config
                late_posting_date_start=minDate,
                late_posting_date_min=minDate,
                late_posting_date_max=maxDate,
                
                saving_multiple=config.saving_multiple,
                shares_multiple=config.shares_multiple,
                social_min=config.social_min,
                
                loan_interest_rate=loan_interest_rate,
                loan_repayment_rate=loan_repayment_rate,
                loan_saving_ratio=config.loan_saving_ratio,
                loan_duration=loan_duration,
                loan_apply_limit=config.loan_apply_limit,
                
                late_posting_rate=config.late_posting_rate,
                missed_meeting_rate=config.missed_meeting_rate,
                late_meeting_rate=config.late_meeting_rate,
                # approval
                status_id=assist.STATUS_DRAFT,
                stage_id=assist.APPROVAL_STAGE_DRAFT,
                approval_levels=config.approval_levels,
            )

            db.add(db_status)

    try:
        await db.commit()
        # await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to initialize posting periods: f{e}"
        )
    return {
        "succeeded": True,
        "message": "Posting periods have been successfully initialized",
    }


@router.get("/list", response_model=List[PostingPeriodWithDetail])
async def list_periods(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PostingPeriodDB).order_by(PostingPeriodDB.id))
    return result.scalars().all()


@router.put("/update/{id}", response_model=PostingPeriodWithDetail)
async def update_meeting(
    id: str, period_update: PostingPeriod, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PostingPeriodDB).where(PostingPeriodDB.id == id))
    period = result.scalar_one_or_none()

    if not period:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find posting period with id '{id}'",
        )

    # Update fields that are not None
    for key, value in period_update.dict(exclude_unset=True).items():
        setattr(period, key, value)

    try:
        await db.commit()
        await db.refresh(period)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update posting period {e}"
        )
    return period


@router.get("/id/{period_id}", response_model=ParamPeriodSummary)
async def get_posting(period_id: str, db: AsyncSession = Depends(get_db)):
    print("starting single period summary", assist.get_current_date(False))

    # get all statuses
    result = await db.execute(select(ReviewStageDB))
    stages = result.scalars().all()

    result = await db.execute(
        select(PostingPeriodDB)
        # .options(
        #    joinedload(MonthlyPostingDB.status),
        # )
        .filter(PostingPeriodDB.id == period_id)
    )
    period = result.scalars().first()
    if not period:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find posting period with id '{period_id}'",
        )

        # create a summary
    summary = {
        "id": period.id,
        "name": period.period_name,
        "year": period.year,
        "month": period.month,
        "cash_at_bank": period.cash_at_bank,
        "late_posting_date_start": period.late_posting_date_start,
        "late_posting_date_min": period.late_posting_date_min,
        "late_posting_date_max": period.late_posting_date_max,
        "saving_multiple": period.saving_multiple,
        "shares_multiple": period.shares_multiple,
        "social_min": period.social_min,
        "loan_interest_rate": period.loan_interest_rate,
        "loan_repayment_rate": period.loan_repayment_rate,
        "loan_saving_ratio": period.loan_saving_ratio,
        "loan_duration": period.loan_duration,
        "loan_apply_limit": period.loan_apply_limit,
        "late_posting_rate": period.late_posting_rate,
        "missed_meeting_rate": period.missed_meeting_rate,
        "late_meeting_rate": period.late_meeting_rate,
        "status_id": period.status_id,
        "status": period.status.status_name,
        "approval_levels": period.approval_levels,
        "stage_id": period.stage_id,
        "stage": period.stage.stage_name,
    }

    # add statistics info
    for status in stages:
        summary[f"sid{status.id}"] = 0

    # get available postings
    stmt = (
        select(
            MonthlyPostingDB.stage_id,
            func.coalesce(func.count(MonthlyPostingDB.period_id), 0).label("total"),
        )
        .filter(
            MonthlyPostingDB.period_id == period_id,
        )
        .group_by(
            MonthlyPostingDB.stage_id,
        )
    )

    result = await db.execute(stmt)
    rows = result.all()

    # map periods to base items

    for statistic in rows:
        sid = statistic["stage_id"]
        summary[f"sid{sid}"] = statistic["total"]

    print("ending single period summary", assist.get_current_date(False))

    return summary


def get_stage_fields(currentStage: int, email: str, comments: str):
    if currentStage == 1:
        return {
            MonthlyPostingDB.review1_at: assist.get_current_date(False),
            MonthlyPostingDB.review1_by: email,
            MonthlyPostingDB.review1_comments: comments,
        }
    elif currentStage == 2:
        return {
            MonthlyPostingDB.review2_at: assist.get_current_date(False),
            MonthlyPostingDB.review2_by: email,
            MonthlyPostingDB.review2_comments: comments,
        }
    else:
        return {
            MonthlyPostingDB.review3_at: assist.get_current_date(False),
            MonthlyPostingDB.review3_by: email,
            MonthlyPostingDB.review3_comments: comments,
        }


async def update_period_postings(
    db: AsyncSession,
    currentPeriod: int,
    reviewAction: int,
    currentStage: int,
    email: str,
    comments: str,
    newStage: int,
    newStatus: int,
):

    # get fields
    # get review fields
    fields = get_stage_fields(currentStage, email, comments)

    # check type of action
    if reviewAction == assist.REVIEW_ACTION_REJECT:

        # reject
        await db.execute(
            update(MonthlyPostingDB)
            .where(
                and_(
                    MonthlyPostingDB.period_id == currentPeriod,
                    MonthlyPostingDB.stage_id == currentStage,
                    MonthlyPostingDB.status_id == assist.STATUS_SUBMITTED,
                )
            )
            .values(fields)
        )

        if newStatus != -1:
            # update the fields

            await db.execute(
                update(MonthlyPostingDB)
                .where(
                    and_(
                        MonthlyPostingDB.period_id == currentPeriod,
                        MonthlyPostingDB.stage_id == currentStage,
                        MonthlyPostingDB.status_id == assist.STATUS_SUBMITTED,
                    )
                )
                .values({MonthlyPostingDB.status_id: assist.STATUS_REJECTED})
            )

        await db.commit()

    else:
        # approve

        # fields
        await db.execute(
            update(MonthlyPostingDB)
            .where(
                and_(
                    MonthlyPostingDB.period_id == currentPeriod,
                    MonthlyPostingDB.stage_id == currentStage,
                    MonthlyPostingDB.status_id == assist.STATUS_SUBMITTED,
                )
            )
            .values(fields)
        )

        # stage
        if newStage != -1:
            # update stage if its not -1
            await db.execute(
                update(MonthlyPostingDB)
                .where(
                    and_(
                        MonthlyPostingDB.period_id == currentPeriod,
                        MonthlyPostingDB.stage_id == currentStage,
                        MonthlyPostingDB.status_id == assist.STATUS_SUBMITTED,
                    )
                )
                .values({MonthlyPostingDB.stage_id: newStage})
            )

        # status
        if newStatus != -1:
            # update status if its not -1
            await db.execute(
                update(MonthlyPostingDB)
                .where(
                    and_(
                        MonthlyPostingDB.period_id == currentPeriod,
                        MonthlyPostingDB.stage_id == currentStage,
                        MonthlyPostingDB.status_id == assist.STATUS_SUBMITTED,
                    )
                )
                .values({MonthlyPostingDB.status_id: newStatus})
            )

        await db.commit()


@router.put("/review-update/{post_id}", response_model=PostingPeriodWithDetail)
async def review_posting(
    post_id: str, review: SACCOReview, db: AsyncSession = Depends(get_db)
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
        select(PostingPeriodDB).where(PostingPeriodDB.id == post_id)
    )
    postingPeriod = result.scalar_one_or_none()

    if not postingPeriod:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find posting period with id '{post_id}' not found",
        )

    if postingPeriod.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The posting period with id '{post_id}' has already been approved",
        )

    # get config
    result = await db.execute(
        select(SACCOConfigurationDB).filter(SACCOConfigurationDB.id == 1)
    )

    config = result.scalars().first()
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to load param: Configuration with id '{1}' not found",
        )

    postingPeriod.updated_by = user.email

    currentStage = postingPeriod.stage_id

    if postingPeriod.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        postingPeriod.review1_at = assist.get_current_date(False)
        postingPeriod.review1_by = user.email
        postingPeriod.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject
            postingPeriod.status_id = assist.STATUS_REJECTED

            # update the postings
            await update_period_postings(
                db,
                post_id,
                review.review_action,
                currentStage,
                user.email,
                review.comments,
                -1,
                assist.STATUS_REJECTED,
            )
        else:
            # approve

            # check number of approval levels
            if config.approval_levels == 1:
                # one level, no furthur stage approvers

                postingPeriod.stage_id = assist.APPROVAL_STAGE_POP_UPLOAD

                # update the postings
                await update_period_postings(
                    db,
                    post_id,
                    review.review_action,
                    currentStage,
                    user.email,
                    review.comments,
                    assist.APPROVAL_STAGE_POP_UPLOAD,
                    -1,
                )

            elif (
                postingPeriod.approval_levels == 2 or postingPeriod.approval_levels == 3
            ):
                # two or three levels, move to primary
                postingPeriod.stage_id = assist.APPROVAL_STAGE_PRIMARY

                # update the postings
                await update_period_postings(
                    db,
                    post_id,
                    review.review_action,
                    currentStage,
                    user.email,
                    review.comments,
                    assist.APPROVAL_STAGE_PRIMARY,
                    -1,
                )

    elif postingPeriod.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage

        postingPeriod.review2_at = assist.get_current_date(False)
        postingPeriod.review2_by = user.email
        postingPeriod.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            postingPeriod.status_id = assist.STATUS_REJECTED

            # update the postings
            await update_period_postings(
                db,
                post_id,
                review.review_action,
                currentStage,
                user.email,
                review.comments,
                -1,
                assist.STATUS_REJECTED,
            )
        else:
            # approve

            # check number of approval levels
            if config.approval_levels == 2:
                # two levels, no furthur stage approvers
                # no guarantor approval
                postingPeriod.stage_id = assist.APPROVAL_STAGE_POP_UPLOAD

                # update the postings
                await update_period_postings(
                    db,
                    post_id,
                    review.review_action,
                    currentStage,
                    user.email,
                    review.comments,
                    assist.APPROVAL_STAGE_POP_UPLOAD,
                    -1,
                )

            elif config.approval_levels == 3:
                # three levels, move to secondary
                postingPeriod.stage_id = assist.APPROVAL_STAGE_SECONDARY

                # update the postings
                await update_period_postings(
                    db,
                    post_id,
                    review.review_action,
                    currentStage,
                    user.email,
                    review.comments,
                    assist.APPROVAL_STAGE_SECONDARY,
                    -1,
                )

    elif postingPeriod.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage

        postingPeriod.review3_at = assist.get_current_date(False)
        postingPeriod.review3_by = user.email
        postingPeriod.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            postingPeriod.status_id = assist.STATUS_REJECTED

            # update the postings
            await update_period_postings(
                db,
                post_id,
                review.review_action,
                currentStage,
                user.email,
                review.comments,
                -1,
                assist.STATUS_REJECTED,
            )
        else:
            # approve
            # three levels and on last stage
            postingPeriod.stage_id = assist.APPROVAL_STAGE_POP_UPLOAD

            # update the postings
            await update_period_postings(
                db,
                post_id,
                review.review_action,
                currentStage,
                user.email,
                review.comments,
                assist.APPROVAL_STAGE_POP_UPLOAD,
                -1,
            )

    elif postingPeriod.stage_id == assist.APPROVAL_STAGE_POP_UPLOAD:
        # pop upload

        postingPeriod.stage_id = assist.APPROVAL_STAGE_POP_APPROVAL
        postingPeriod.pop_comments = review.comments

        # no need to update postings, the user will upload pop and force the stage to move

    elif postingPeriod.stage_id == assist.APPROVAL_STAGE_POP_APPROVAL:
        # move to approved and post transactions

        postingPeriod.pop_review_at = assist.get_current_date(False)
        postingPeriod.pop_review_by = user.email
        postingPeriod.pop_review_comments = review.comments

        postingPeriod.status_id = assist.STATUS_APPROVED
        postingPeriod.stage_id = assist.APPROVAL_STAGE_APPROVED

        # no need to update postings, the admin will approve the pop and force the stage to move
        # this will also post the transactions

    try:
        await db.commit()
        await db.refresh(postingPeriod)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update posting period: {e}"
        )
    return postingPeriod


@router.get(
    "/year/{year}/month/{month}/status/{status_id}",
    response_model=List[ParamPeriodSummary],
)
async def list_current_periods(
    year: int, month: int, status_id: int, db: AsyncSession = Depends(get_db)
):
    print("starting period summary", assist.get_current_date(False))
    # get all statuses
    result = await db.execute(select(ReviewStageDB))
    stages = result.scalars().all()

    filterYear = year
    filterMonth = month

    if status_id == 0:
        result = await db.execute(
            select(PostingPeriodDB).filter(
                PostingPeriodDB.year == filterYear, PostingPeriodDB.month <= filterMonth
            )
        )
    else:
        result = await db.execute(
            select(PostingPeriodDB).filter(
                PostingPeriodDB.year == filterYear,
                PostingPeriodDB.month <= filterMonth,
                PostingPeriodDB.status_id == status_id,
            )
        )

    periods = result.scalars().all()

    # create a summary
    summary = [
        {
            "id": period.id,
            "name": period.period_name,
            "year": period.year,
            "month": period.month,
            "cash_at_bank": period.cash_at_bank,
            "late_posting_date_start": period.late_posting_date_start,
            "late_posting_date_min": period.late_posting_date_min,
            "late_posting_date_max": period.late_posting_date_max,
            "saving_multiple": period.saving_multiple,
            "shares_multiple": period.shares_multiple,
            "social_min": period.social_min,
            "loan_interest_rate": period.loan_interest_rate,
            "loan_repayment_rate": period.loan_repayment_rate,
            "loan_saving_ratio": period.loan_saving_ratio,
            "loan_duration": period.loan_duration,
            "loan_apply_limit": period.loan_apply_limit,
            "late_posting_rate": period.late_posting_rate,
            "missed_meeting_rate": period.missed_meeting_rate,
            "late_meeting_rate": period.late_meeting_rate,
            "status_id": period.status_id,
            "status": period.status.status_name,
            "approval_levels": period.approval_levels,
            "stage_id": period.stage_id,
            "stage": period.stage.stage_name,
        }
        for period in periods
    ]

    # add statistics info
    for period in summary:
        for status in stages:
            period[f"sid{status.id}"] = 0

    # get available postings
    period_date = dt.datetime(year, month, 1)
    period_id = assist.get_date_period(period_date)
    stmt = (
        select(
            MonthlyPostingDB.period_id,
            MonthlyPostingDB.stage_id,
            func.coalesce(func.count(MonthlyPostingDB.period_id), 0).label("total"),
        )
        .filter(
            MonthlyPostingDB.period_id <= period_id,
        )
        .group_by(
            MonthlyPostingDB.period_id,
            MonthlyPostingDB.stage_id,
        )
    )

    result = await db.execute(stmt)
    rows = result.all()

    # map periods to base items
    for period in summary:
        for statistic in rows:
            if period["id"] == statistic["period_id"]:
                sid = statistic["stage_id"]
                period[f"sid{sid}"] = statistic["total"]

    print("ending period summary", assist.get_current_date(False))

    return summary


@router.get("/ddac/{period_id}", response_model=List[MonthlyPostingWithMemberDetail])
async def list_current_periods(period_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonthlyPostingDB)
        # .options(
        #    joinedload(MonthlyPostingDB.status),
        # )
        .filter(
            MonthlyPostingDB.period_id == period_id,
            MonthlyPostingDB.status_id == assist.STATUS_APPROVED,
            MonthlyPostingDB.receive_total > 0,
        )
    )
    postings = result.scalars().all()
    return postings
