import os
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from helpers import assist
from models.attachment_model import AttachmentDB
from models.meeting_model import Meeting, MeetingDB, MeetingWithDetail
from models.review_model import SACCOReview
from models.user_model import UserDB
import csv

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.post("/create", response_model=Meeting)
async def post_meeting(meeting: Meeting, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == meeting.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"User with id {meeting.user_id} does not exist"
        )

    db_tran = MeetingDB(
        # user
        user_id=meeting.user_id,
        # attachment
        attachment_id=meeting.attachment_id,
        # meeting
        date=meeting.date,
        title=meeting.title,
        content=meeting.content,
        # approval
        status_id=meeting.status_id,
        stage_id=meeting.stage_id,
        approval_levels=meeting.approval_levels,
        # service
        created_by=meeting.created_by,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not create meeting: {e}")
    return db_tran


@router.get("/list", response_model=List[MeetingWithDetail])
async def list_meetings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MeetingDB)
        # .options(
        #    joinedload(MeetingDB.post),
        #    joinedload(MeetingDB.status),
        #    joinedload(MeetingDB.type),
        #    joinedload(MeetingDB.source),
        #
        # )
    )
    meetings = result.scalars().all()
    return meetings


@router.put("/update/{id}", response_model=MeetingWithDetail)
async def update_meeting(
    id: int, meeting_update: Meeting, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MeetingDB).where(MeetingDB.id == id))
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find meeting with id '{id}'",
        )

    # Update fields that are not None
    for key, value in meeting_update.dict(exclude_unset=True).items():
        setattr(meeting, key, value)

    try:
        await db.commit()
        await db.refresh(meeting)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update meeting {e}")
    return meeting


@router.get("/id/{meeting_id}", response_model=MeetingWithDetail)
async def get_meeting(meeting_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MeetingDB)
        # .options(
        #    joinedload(MeetingDB.post),
        #    joinedload(MeetingDB.status),
        #    joinedload(MeetingDB.type),
        #    joinedload(MeetingDB.source),
        #
        # )
        .filter(MeetingDB.id == meeting_id)
    )
    meeting = result.scalars().first()
    if not meeting:
        raise HTTPException(
            status_code=404, detail=f"Meeting with id '{meeting_id}' not found"
        )

    return meeting


@router.put("/review-update/{id}", response_model=MeetingWithDetail)
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
    result = await db.execute(select(MeetingDB).where(MeetingDB.id == id))
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find meeting with id '{id}' not found",
        )

    if meeting.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The meeting with id '{id}' has already been approved",
        )

    meeting.updated_by = user.email

    approveMeeting = False

    if meeting.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        meeting.review1_at = assist.get_current_date(False)
        meeting.review1_by = user.email
        meeting.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            meeting.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if meeting.approval_levels == 1:
                # one level, no furthur stage approvers

                # approve meeting
                approveMeeting = True

            elif meeting.approval_levels == 2 or meeting.approval_levels == 3:
                # two or three levels, move to primary

                meeting.stage_id = assist.APPROVAL_STAGE_PRIMARY

    elif meeting.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage

        meeting.review2_at = assist.get_current_date(False)
        meeting.review2_by = user.email
        meeting.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            meeting.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if meeting.approval_levels == 2:
                # two levels, no furthur stage approvers

                approveMeeting = True

            elif meeting.approval_levels == 3:
                # three levels, move to secondary
                meeting.stage_id = assist.APPROVAL_STAGE_SECONDARY

    elif meeting.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage

        meeting.review3_at = assist.get_current_date(False)
        meeting.review3_by = user.email
        meeting.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            meeting.status_id = assist.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage
            approveMeeting = True

    if approveMeeting:
        # change meeting status
        meeting.status_id = assist.STATUS_APPROVED
        meeting.stage_id = assist.APPROVAL_STAGE_APPROVED

        # get attachment
        result = await db.execute(
            select(AttachmentDB).filter(AttachmentDB.id == meeting.attachment_id)
        )
        attachment = result.scalars().first()
        if not attachment:
            raise HTTPException(
                status_code=404, detail=f"Attachment with id '{id}' not found"
            )

        # post meeting attendance
        try:
            with open(f"my_file.txt", "r") as file:
                content = file.read()
                print(content)
        except FileNotFoundError:
            print("Error: The file 'my_file.txt' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    try:
        await db.commit()
        await db.refresh(meeting)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update meeting: {e}")
    return meeting
