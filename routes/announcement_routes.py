from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from helpers import assist
from models.annoucement_model import Announcement, AnnouncementDB, AnnouncementWithDetail
from models.attachment_model import AttachmentDB
from models.review_model import SACCOReview
from models.user_model import UserDB
from sqlalchemy import desc

router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.post("/create", response_model=Announcement)
async def post_announcement(announcement: Announcement, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == announcement.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{announcement.user_id}' does not exist"
        )

    db_tran = AnnouncementDB(
        # user
        user_id = announcement.user_id,
        # transaction
        title = announcement.title,
        content = announcement.content,
        # attachment
        attachment_id=announcement.attachment_id,
        # approval
        status_id = announcement.status_id,
        stage_id = announcement.stage_id,
        approval_levels = announcement.approval_levels,
        # service
        created_by=user.email,
  
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create announcement: {e}")
    return db_tran

@router.put("/update/{config_id}", response_model=AnnouncementWithDetail)
async def update_configuration(config_id: int, config_update: Announcement, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AnnouncementDB)
        .where(AnnouncementDB.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Unable to find announcement with id '{config_id}'")
    
    # Update fields that are not None
    for key, value in config_update.dict(exclude_unset=True).items():
        setattr(config, key, value)
        
    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update announcement {e}")
    return config


@router.get("/list", response_model=List[AnnouncementWithDetail])
async def list_announcements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AnnouncementDB)
        #.options(
        #    joinedload(AnnouncementDB.post),
        #    joinedload(AnnouncementDB.status),
        #    joinedload(AnnouncementDB.type),
        #    joinedload(AnnouncementDB.source),
        #
        #)
    )
    announcements = result.scalars().all()
    return announcements

@router.get("/recent", response_model=List[AnnouncementWithDetail])
async def list_recent_announcements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AnnouncementDB)
        .where(
            AnnouncementDB.status_id == assist.STATUS_APPROVED,
        )
        .limit(3)
        .order_by(desc(AnnouncementDB.id))
    )
    announcements = result.scalars().all()
    return announcements

@router.get("/id/{announcement_id}", response_model=AnnouncementWithDetail)
async def get_announcement(announcement_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AnnouncementDB)
        #.options(
        #    joinedload(AnnouncementDB.post),
        #    joinedload(AnnouncementDB.status),
        #    joinedload(AnnouncementDB.type),
        #    joinedload(AnnouncementDB.source),
        #
        #)
        .filter(AnnouncementDB.id == announcement_id)
    )
    announcement = result.scalars().first()
    if not announcement:
        raise HTTPException(status_code=404, detail=f"Unable to find announcement with id '{announcement_id}'")
    return announcement



@router.put("/review-update/{id}", response_model=AnnouncementWithDetail)
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
    result = await db.execute(select(AnnouncementDB).where(AnnouncementDB.id == id))
    announcement = result.scalar_one_or_none()

    if not announcement:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find announcement with id '{id}' not found",
        )

    if announcement.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The announcement with id '{id}' has already been approved",
        )

    announcement.updated_by = user.email

    approveMeeting = False

    if announcement.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage
        
        if announcement.created_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the primary reviewer of an announcement you created",
        )

        announcement.review1_at = assist.get_current_date(False)
        announcement.review1_by = user.email
        announcement.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            announcement.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if announcement.approval_levels == 1:
                # one level, no furthur stage approvers

                # approve announcement
                approveMeeting = True

            elif announcement.approval_levels == 2 or announcement.approval_levels == 3:
                # two or three levels, move to primary

                announcement.stage_id = assist.APPROVAL_STAGE_PRIMARY

    elif announcement.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage
        
        if announcement.review1_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the secondary reviewer since you were the primary reviewer",
        )

        announcement.review2_at = assist.get_current_date(False)
        announcement.review2_by = user.email
        announcement.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            announcement.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if announcement.approval_levels == 2:
                # two levels, no furthur stage approvers

                approveMeeting = True

            elif announcement.approval_levels == 3:
                # three levels, move to secondary
                announcement.stage_id = assist.APPROVAL_STAGE_SECONDARY

    elif announcement.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage
        
        if announcement.review2_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the final reviewer since you were the secondary reviewer",
        )

        announcement.review3_at = assist.get_current_date(False)
        announcement.review3_by = user.email
        announcement.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            announcement.status_id = assist.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage
            approveMeeting = True

    if approveMeeting:
        # change announcement status
        announcement.status_id = assist.STATUS_APPROVED
        announcement.stage_id = assist.APPROVAL_STAGE_APPROVED

        # attachment may or may not be provided

    try:
        await db.commit()
        await db.refresh(announcement)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update announcement: {e}")
    return announcement
