from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from helpers import assist
from models.member_model import MemberDB
from models.guarantor_model import Guarantor, GuarantorDB, GuarantorWithDetail
from models.attachment_model import AttachmentDB
from models.review_model import SACCOReview
from models.user_model import UserDB
from sqlalchemy import desc

router = APIRouter(prefix="/guarantors", tags=["Guarantors"])


@router.post("/create", response_model=Guarantor)
async def post_guarantor(guarantor: Guarantor, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(MemberDB).where(MemberDB.id == guarantor.user_id))
    member = result.scalars().first()
    
    if not member:
        raise HTTPException(
            status_code=400, detail=f"The member with id '{guarantor.user_id}' does not exist"
        )
        
        
    db_tran = GuarantorDB(
        # user
        user_id=member.user_id,
        member_id=member.id,
        # guarantor
        guar_fname=guarantor.guar_fname,
        guar_lname=guarantor.guar_lname,
        guar_code=guarantor.guar_code,
        guar_mobile=guarantor.guar_mobile,
        guar_email=guarantor.guar_email,
        # approval
        status_id=guarantor.status_id,
        stage_id=guarantor.stage_id,
        approval_levels=guarantor.approval_levels,
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
            status_code=400, detail=f"Unable to create gurantor: {e}"
        )
    return db_tran


@router.put("/update/{config_id}", response_model=GuarantorWithDetail)
async def update_configuration(
    config_id: int, config_update: Guarantor, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(GuarantorDB).where(GuarantorDB.id == config_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"Unable to find guarantor with id '{config_id}'"
        )

    # Update fields that are not None
    for key, value in config_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update guarantor {e}")
    return config


@router.get("/list", response_model=List[GuarantorWithDetail])
async def list_guarantors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GuarantorDB)
    )
    guarantors = result.scalars().all()
    return guarantors

@router.get("/user/{user_id}/list", response_model=List[GuarantorWithDetail])
async def list_my_guarantors(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GuarantorDB)
       .filter(GuarantorDB.user_id == user_id)
    )
    guarantors = result.scalars().all()
    return guarantors

@router.get("/id/{guarantor_id}", response_model=GuarantorWithDetail)
async def get_guarantor(guarantor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GuarantorDB)
        .filter(GuarantorDB.id == guarantor_id)
    )
    guarantor = result.scalars().first()
    if not guarantor:
        raise HTTPException(
            status_code=404, detail=f"Unable to find guarantor with id '{guarantor_id}'"
        )
    return guarantor


@router.put("/review-update/{id}", response_model=GuarantorWithDetail)
async def review_posting(
    id: int, review: SACCOReview, db: AsyncSession = Depends(get_db)
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
    result = await db.execute(select(GuarantorDB).where(GuarantorDB.id == id))
    guarantor = result.scalar_one_or_none()

    if not guarantor:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find guarantor with id '{id}' not found",
        )

    if guarantor.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The guarantor with id '{id}' has already been approved",
        )

    guarantor.updated_by = user.email

    approveMeeting = False

    if guarantor.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        if guarantor.created_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the primary reviewer of an guarantor you created",
            )

        guarantor.review1_at = assist.get_current_date(False)
        guarantor.review1_by = user.email
        guarantor.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            guarantor.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if guarantor.approval_levels == 1:
                # one level, no furthur stage approvers

                # approve guarantor
                approveMeeting = True

            elif guarantor.approval_levels == 2 or guarantor.approval_levels == 3:
                # two or three levels, move to primary

                guarantor.stage_id = assist.APPROVAL_STAGE_PRIMARY

    elif guarantor.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage

        if guarantor.review1_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the secondary reviewer since you were the primary reviewer",
            )

        guarantor.review2_at = assist.get_current_date(False)
        guarantor.review2_by = user.email
        guarantor.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            guarantor.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if guarantor.approval_levels == 2:
                # two levels, no furthur stage approvers

                approveMeeting = True

            elif guarantor.approval_levels == 3:
                # three levels, move to secondary
                guarantor.stage_id = assist.APPROVAL_STAGE_SECONDARY

    elif guarantor.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage

        if guarantor.review2_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the final reviewer since you were the secondary reviewer",
            )

        guarantor.review3_at = assist.get_current_date(False)
        guarantor.review3_by = user.email
        guarantor.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            guarantor.status_id = assist.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage
            approveMeeting = True

    if approveMeeting:
        # change guarantor status
        guarantor.status_id = assist.STATUS_APPROVED
        guarantor.stage_id = assist.APPROVAL_STAGE_APPROVED

        # attachment may or may not be provided

    try:
        await db.commit()
        await db.refresh(guarantor)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update guarantor: {e}")
    return guarantor
