from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.osawe.osawedb import get_osawe_db
from helpers import assist
from apps.osawe.models.member_model import MemberDB
from apps.osawe.models.payment_method_model import (
    PaymentMethodDB,
    PaymentMethod,
    PaymentMethodWithDetail,
)
from apps.osawe.models.attachment_model import AttachmentDB
from apps.osawe.models.review_model import SACCOReview
from apps.osawe.models.user_model import UserDB
from sqlalchemy import desc

router = APIRouter(prefix="/paymentmethods", tags=["PaymentMethods"])


@router.post("/create", response_model=PaymentMethod)
async def post_paymentmethod(
    paymentmethod: PaymentMethod, db: AsyncSession = Depends(get_osawe_db)
):
    # check user exists
    result = await db.execute(
        select(MemberDB).where(MemberDB.id == paymentmethod.user_id)
    )
    member = result.scalars().first()

    if not member:
        raise HTTPException(
            status_code=400,
            detail=f"The member with id '{paymentmethod.user_id}' does not exist",
        )

    db_tran = PaymentMethodDB(
        # user
        user_id=member.user_id,
        member_id=member.id,
        # details
        name=paymentmethod.name,
        type=paymentmethod.type,
        # mobile
        method_code=paymentmethod.method_code,
        method_number=paymentmethod.method_number,
        method_name=paymentmethod.method_name,
        # banking
        bank_name=paymentmethod.bank_name,
        bank_branch_name=paymentmethod.bank_branch_name,
        bank_branch_code=paymentmethod.bank_branch_code,
        bank_account_name=paymentmethod.bank_account_name,
        bank_account_no=paymentmethod.bank_account_no,
        # approval
        status_id=paymentmethod.status_id,
        stage_id=paymentmethod.stage_id,
        approval_levels=paymentmethod.approval_levels,
        # service
        created_by=member.email,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to create payment method: {e}"
        )
    return db_tran


@router.put("/update/{config_id}", response_model=PaymentMethodWithDetail)
async def update_item(
    config_id: int, config_update: PaymentMethod, db: AsyncSession = Depends(get_osawe_db)
):
    result = await db.execute(
        select(PaymentMethodDB).where(PaymentMethodDB.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find paymentmethod with id '{config_id}'",
        )

    # Update fields that are not None
    for key, value in config_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update paymentmethod {e}"
        )
    return config


@router.get("/list", response_model=List[PaymentMethodWithDetail])
async def list_paymentmethods(db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(select(PaymentMethodDB))
    paymentmethods = result.scalars().all()
    return paymentmethods


@router.get("/user/{user_id}/list", response_model=List[PaymentMethodWithDetail])
async def list_my_paymentmethods(user_id: int, db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(
        select(PaymentMethodDB).filter(PaymentMethodDB.user_id == user_id)
    )
    paymentmethods = result.scalars().all()
    return paymentmethods


@router.get(
    "/user/{user_id}/approved/list", response_model=List[PaymentMethodWithDetail]
)
async def list_my_approved_paymentmethods(
    user_id: int, db: AsyncSession = Depends(get_osawe_db)
):
    result = await db.execute(
        select(PaymentMethodDB).filter(
            PaymentMethodDB.user_id == user_id,
            PaymentMethodDB.status_id == assist.STATUS_APPROVED,
        )
    )
    paymentmethods = result.scalars().all()
    return paymentmethods


@router.get("/id/{paymentmethod_id}", response_model=PaymentMethodWithDetail)
async def get_paymentmethod(paymentmethod_id: int, db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(
        select(PaymentMethodDB).filter(PaymentMethodDB.id == paymentmethod_id)
    )
    paymentmethod = result.scalars().first()
    if not paymentmethod:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find paymentmethod with id '{paymentmethod_id}'",
        )
    return paymentmethod


@router.put("/review-update/{id}", response_model=PaymentMethodWithDetail)
async def review_posting(
    id: int, review: SACCOReview, db: AsyncSession = Depends(get_osawe_db)
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == review.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{review.user_id}' does not exist",
        )

    # check if item exists
    result = await db.execute(select(PaymentMethodDB).where(PaymentMethodDB.id == id))
    paymentmethod = result.scalar_one_or_none()

    if not paymentmethod:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find paymentmethod with id '{id}' not found",
        )

    if paymentmethod.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The paymentmethod with id '{id}' has already been approved",
        )

    paymentmethod.updated_by = user.email

    approveMeeting = False

    if paymentmethod.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        if paymentmethod.created_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the primary reviewer of an paymentmethod you created",
            )

        paymentmethod.review1_at = assist.get_current_date(False)
        paymentmethod.review1_by = user.email
        paymentmethod.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            paymentmethod.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if paymentmethod.approval_levels == 1:
                # one level, no furthur stage approvers

                # approve paymentmethod
                approveMeeting = True

            elif (
                paymentmethod.approval_levels == 2 or paymentmethod.approval_levels == 3
            ):
                # two or three levels, move to primary

                paymentmethod.stage_id = assist.APPROVAL_STAGE_PRIMARY

    elif paymentmethod.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage

        if paymentmethod.review1_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the secondary reviewer since you were the primary reviewer",
            )

        paymentmethod.review2_at = assist.get_current_date(False)
        paymentmethod.review2_by = user.email
        paymentmethod.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            paymentmethod.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if paymentmethod.approval_levels == 2:
                # two levels, no furthur stage approvers

                approveMeeting = True

            elif paymentmethod.approval_levels == 3:
                # three levels, move to secondary
                paymentmethod.stage_id = assist.APPROVAL_STAGE_SECONDARY

    elif paymentmethod.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage

        if paymentmethod.review2_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the final reviewer since you were the secondary reviewer",
            )

        paymentmethod.review3_at = assist.get_current_date(False)
        paymentmethod.review3_by = user.email
        paymentmethod.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            paymentmethod.status_id = assist.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage
            approveMeeting = True

    if approveMeeting:
        # change paymentmethod status
        paymentmethod.status_id = assist.STATUS_APPROVED
        paymentmethod.stage_id = assist.APPROVAL_STAGE_APPROVED

        # attachment may or may not be provided

    try:
        await db.commit()
        await db.refresh(paymentmethod)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update paymentmethod: {e}"
        )
    return paymentmethod
