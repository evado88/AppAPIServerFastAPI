from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.osawe.osawedb import get_osawe_db
from helpers import assist
from apps.osawe.models.review_model import SACCOReview
from apps.osawe.models.user_model import User, UserDB, UserSimple, UserWithDetail

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/create", response_model=User)
async def create_user(user: User, db: AsyncSession = Depends(get_osawe_db)):
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
        mobile_code=user.mobile_code,
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
        created_by=user.created_by,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create user: f{e}")
    return db_user


@router.put("/update/{user_id}", response_model=UserWithDetail)
async def update_item(
    user_id: int, config_update: User, db: AsyncSession = Depends(get_osawe_db)
):
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"Unable to find user with id '{user_id}'"
        )

    # Update fields that are not None
    for key, value in config_update.dict(exclude_unset=True).items():
        # if password, encrypt
        if key == "password":
            setattr(config, key, assist.hash_password(value))
        else:
            setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update user {e}")
    return config


@router.get("/id/{user_id}", response_model=UserWithDetail)
async def get_user_id(user_id: int, db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(select(UserDB).filter(UserDB.id == user_id))
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(
            status_code=404, detail=f"Unable to find user with specified id '{user_id}'"
        )
    return transaction


@router.get("/email/{user_email}", response_model=List[UserSimple])
async def get_user_email(user_email: str, db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(select(UserDB).filter(UserDB.email == user_email))
    users = []

    user = result.scalars().first()
    if user:
        users.append(user)

    return users


@router.get("/list", response_model=List[UserWithDetail])
async def list_users(db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(select(UserDB))
    return result.scalars().all()


@router.put("/update-password", response_model=UserSimple)
async def login(
    username: str = Form(...),
    current_password: str = Form(...),
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_osawe_db),
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.email == username))
    user = result.scalars().first()

    if not user:
        # user not found
        raise HTTPException(status_code=401, detail=f"The specified username incorrect")

    if not assist.verify_password(current_password, user.password):
        raise HTTPException(
            status_code=401, detail=f"The specified current password is incorrect"
        )

    user.password = assist.hash_password(new_password)

    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update user: {e}")
    return user


@router.put("/review-update/{id}", response_model=UserWithDetail)
async def review_posting(
    id: int, review: SACCOReview, db: AsyncSession = Depends(get_osawe_db)
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == review.user_id))
    approveUser = result.scalars().first()
    if not approveUser:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{review.user_id}' does not exist",
        )

    # check if item exists
    result = await db.execute(select(UserDB).where(UserDB.id == id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find user with id '{id}' not found",
        )

    if user.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{id}' has already been approved",
        )

    user.updated_by = approveUser.email

    approveMeeting = False

    if user.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        if user.created_by == approveUser.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the primary reviewer of an user you created",
            )

        user.review1_at = assist.get_current_date(False)
        user.review1_by = approveUser.email
        user.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            user.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if user.approval_levels == 1:
                # one level, no furthur stage approvers

                # approve user
                approveMeeting = True

            elif user.approval_levels == 2 or user.approval_levels == 3:
                # two or three levels, move to primary

                user.stage_id = assist.APPROVAL_STAGE_PRIMARY

    elif user.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage

        if user.review1_by == approveUser.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the secondary reviewer since you were the primary reviewer",
            )

        user.review2_at = assist.get_current_date(False)
        user.review2_by = approveUser.email
        user.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            user.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if user.approval_levels == 2:
                # two levels, no furthur stage approvers

                approveMeeting = True

            elif user.approval_levels == 3:
                # three levels, move to secondary
                user.stage_id = assist.APPROVAL_STAGE_SECONDARY

    elif user.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage

        if user.review2_by == approveUser.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the final reviewer since you were the secondary reviewer",
            )

        user.review3_at = assist.get_current_date(False)
        user.review3_by = approveUser.email
        user.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            user.status_id = assist.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage
            approveMeeting = True

    if approveMeeting:
        # change user status
        user.status_id = assist.STATUS_APPROVED
        user.stage_id = assist.APPROVAL_STAGE_APPROVED

        # attachment may or may not be provided

    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update user: {e}")
    return user
