from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.meter_reading_model import (
    MeterReading,
    MeterReadingDB,
    MeterReadingWithDetail,
)
from apps.lwsc.models.user_model import UserDB

router = APIRouter(prefix="/meter-readings", tags=["MeterReadings"])

async def create_meterreading(meterreading: MeterReading, db: AsyncSession):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == meterreading.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{meterreading.user_id}' does not exist",
        )

    db_user = MeterReadingDB(
        # uuid
        uuid=meterreading.uuid,
        # user
        user_id=meterreading.user_id,
        # attachment
        attachment_id=meterreading.attachment_id,
        # customer
        customer_id=meterreading.customer_id,
        # meter
        meter_id=meterreading.meter_id,
        # details
        read_date=meterreading.read_date,
        current=meterreading.current,
        previous=meterreading.previous,
        comments=meterreading.comments,
        # addres
        lon=meterreading.lat,
        lat=meterreading.lon,
        # approval
        status_id=meterreading.status_id,
        stage_id=meterreading.stage_id,
        approval_levels=meterreading.approval_levels,
        # service
        created_by=user.email,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to create meterreading: f{e}"
        )
        
    return db_user

async def update_meterreading(meterreading_id: int, meterreading_update: MeterReading, db: AsyncSession):
    result = await db.execute(
        select(MeterReadingDB).where(MeterReadingDB.id == meterreading_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find meterreading with id '{meterreading_id}'",
        )

    # Update fields that are not None
    for key, value in meterreading_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update meterreading {e}"
        )
    return config
        
        
@router.post("/upload", response_model=MeterReadingWithDetail)
async def upload_meterreading(meterreading: MeterReading, db: AsyncSession = Depends(get_lwsc_db)):
    # check if reading with same uuid exists
    result = await db.execute(select(MeterReadingDB).where(MeterReadingDB.uuid == meterreading.uuid))
    existing = result.scalars().first()     
    if existing:
        # update existing record instead of creating new one
        return await update_meterreading(existing.id, meterreading, db)
    else:
        # create new record
        return await create_meterreading(meterreading, db)
    

@router.post("/create", response_model=MeterReadingWithDetail)
async def create_new(meterreading: MeterReading, db: AsyncSession = Depends(get_lwsc_db)):
    # check if reading with same uuid exists
    return await create_meterreading(meterreading, db)

        
@router.put("/update/{meterreading_id}", response_model=MeterReadingWithDetail)
async def update_existing(
    meterreading_id: int,
    meterreading_update: MeterReading,
    db: AsyncSession = Depends(get_lwsc_db),
):
    return await update_meterreading(meterreading_id, meterreading_update, db)
    

@router.get("/id/{meterreading_id}", response_model=MeterReadingWithDetail)
async def get_knowledgebase_category(
    meterreading_id: int, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(
        select(MeterReadingDB).filter(MeterReadingDB.id == meterreading_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find meterreading with id '{meterreading_id}'",
        )
    return category





@router.get("/list", response_model=List[MeterReadingWithDetail])
async def list_meterreadings(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(MeterReadingDB))
    return result.scalars().all()
