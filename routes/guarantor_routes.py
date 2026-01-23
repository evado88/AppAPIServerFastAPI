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
            status_code=400,
            detail=f"The member with id '{guarantor.user_id}' does not exist",
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
        raise HTTPException(status_code=400, detail=f"Unable to create gurantor: {e}")
    return db_tran


@router.put("/update/{config_id}", response_model=GuarantorWithDetail)
async def update_item(
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
    result = await db.execute(select(GuarantorDB))
    guarantors = result.scalars().all()
    return guarantors


@router.get("/user/{user_id}/list", response_model=List[GuarantorWithDetail])
async def list_my_guarantors(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GuarantorDB).filter(
            GuarantorDB.user_id == user_id,
        )
    )
    guarantors = result.scalars().all()
    return guarantors

@router.get("/user/{user_id}/approved/list", response_model=List[GuarantorWithDetail])
async def list_my_approved_guarantors(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GuarantorDB).filter(
            GuarantorDB.user_id == user_id,
            GuarantorDB.status_id == assist.STATUS_APPROVED
        )
    )
    guarantors = result.scalars().all()
    return guarantors

@router.get("/email/{email}/list", response_model=List[GuarantorWithDetail])
async def list_email_guarantors(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GuarantorDB).filter(GuarantorDB.guar_email == email)
    )
    guarantors = result.scalars().all()
    return guarantors


@router.get("/id/{guarantor_id}", response_model=GuarantorWithDetail)
async def get_guarantor(guarantor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GuarantorDB).filter(GuarantorDB.id == guarantor_id)
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

    if guarantor.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        if guarantor.created_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the approver of a guarantor you created",
            )

        guarantor.review1_at = assist.get_current_date(False)
        guarantor.review1_by = user.email
        guarantor.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            guarantor.status_id = assist.STATUS_REJECTED
        else:
            # approve

            guarantor.status_id = assist.STATUS_APPROVED
            guarantor.stage_id = assist.APPROVAL_STAGE_APPROVED

    try:
        await db.commit()
        await db.refresh(guarantor)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update guarantor: {e}")
    return guarantor
