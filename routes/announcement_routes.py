from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.annoucement_model import Announcement, AnnouncementDB, AnnouncementWithDetail
from models.user_model import UserDB

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

        # approval
        status_id = announcement.status_id,
        stage_id = announcement.stage_id,
        approval_levels = announcement.approval_levels,
  
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
    for key, value in config_update.model_dump(exclude_unset=True).items():
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
    transactions = result.scalars().all()
    return transactions


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
