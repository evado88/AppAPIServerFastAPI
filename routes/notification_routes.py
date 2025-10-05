from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from database import get_db
from models.notification_model import Notification, NotificationDB, NotificationWithDetail
from models.user_model import UserDB

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/", response_model=Notification)
async def post_notification(notificcation: Notification, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == notificcation.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"User with id {notificcation.user_id} does not exist"
        )

    db_tran = NotificationDB(
        # user
        user_id = notificcation.user_id,
        # transaction

        title = notificcation.title,
        content = notificcation.content,

        # approval
        status_id=notificcation.status_id,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not create notification: {e}")
    return db_tran


@router.get("/", response_model=List[NotificationWithDetail])
async def list_notifications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NotificationDB)
        #.options(
        #    joinedload(NotificationDB.post),
        #    joinedload(NotificationDB.status),
        #    joinedload(NotificationDB.type),
        #    joinedload(NotificationDB.source),
        #
        #)
    )
    transactions = result.scalars().all()
    return transactions


@router.get("/{notification_id}", response_model=NotificationWithDetail)
async def get_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NotificationDB)
        #.options(
        #    joinedload(NotificationDB.post),
        #    joinedload(NotificationDB.status),
        #    joinedload(NotificationDB.type),
        #    joinedload(NotificationDB.source),
        #
        #)
        .filter(NotificationDB.id == notification_id)
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(status_code=404, detail=f"Notification with id '{notification_id}' not found")
    return transaction
