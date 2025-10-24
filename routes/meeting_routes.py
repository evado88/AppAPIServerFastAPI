from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.meeting_model import Meeting, MeetingDB, MeetingWithDetail
from models.user_model import UserDB

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.post("/", response_model=Meeting)
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
        user_id = meeting.user_id,
        
        # meeting
        date = meeting.date,
        title = meeting.title,
        content = meeting.content,

        # approval
        status_id = meeting.status_id,
        stage_id = meeting.stage_id,
        approval_levels = meeting.approval_levels,
        
        #service
        created_by = meeting.created_by,
    
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
        #.options(
        #    joinedload(MeetingDB.post),
        #    joinedload(MeetingDB.status),
        #    joinedload(MeetingDB.type),
        #    joinedload(MeetingDB.source),
        #
        #)
    )
    meetings = result.scalars().all()
    return meetings


@router.get("/{meeting_id}", response_model=MeetingWithDetail)
async def get_meeting(meeting_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MeetingDB)
        #.options(
        #    joinedload(MeetingDB.post),
        #    joinedload(MeetingDB.status),
        #    joinedload(MeetingDB.type),
        #    joinedload(MeetingDB.source),
        #
        #)
        .filter(MeetingDB.id == meeting_id)
    )
    meeting = result.scalars().first()
    if not meeting:
        raise HTTPException(status_code=404, detail=f"Meeting with id '{meeting_id}' not found")
    return meeting
