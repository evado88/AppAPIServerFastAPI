from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy import desc
from sqlalchemy.orm import selectinload, noload
from apps.lwsc import lwscapp
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.bill_rate_model import BillRateDB
from apps.lwsc.models.customer_model import CustomerDB
from apps.lwsc.models.meter_reading_model import (
    MeterReading,
    MeterReadingDB,
    MeterReadingWithDetail,
)
from apps.lwsc.models.user_model import UserDB
from helpers import assist
import random
from sqlalchemy import or_, desc

router = APIRouter(prefix="/meter-readings", tags=["MeterReadings"])


async def get_consumption_zmw(meterreading: MeterReading, db: AsyncSession):
    # get customer id and use it to check categories
    result = await db.execute(
        select(CustomerDB)
        .options(noload("*"))
        .where(CustomerDB.id == meterreading.customer_id)
    )
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find customer with id '{meterreading.customer_id}'",
        )

    # get bill rates
    result = await db.execute(
        select(BillRateDB).where(BillRateDB.cat_id == customer.cat_id)
    )

    rates = result.scalars().all()

    # find the previous reading that is approved
    result = await db.execute(
        select(MeterReadingDB)
        .options(noload("*"))
        .where(MeterReadingDB.uuid != meterreading.uuid,
               MeterReadingDB.customer_id == meterreading.customer_id,
               MeterReadingDB.status_id == assist.STATUS_APPROVED)
        .order_by(desc(MeterReadingDB.read_date))
        .limit(2)
    )
    previousReading = result.scalars().first()

    if previousReading:
        # reading available. calculate consumption
        consumptionM3 = meterreading.current - previousReading.current
        consumptionZMW = lwscapp.get_consumption_rate(consumptionM3, rates)

        # update valeus for current
        meterreading.previous = previousReading.current
        meterreading.consumption_m3 = consumptionM3
        meterreading.consumption_zmw = consumptionZMW

    return meterreading


async def create_meterreading(meterreading: MeterReading, db: AsyncSession):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == meterreading.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{meterreading.user_id}' does not exist",
        )
        
    # look for consumption
    meterreading = await get_consumption_zmw(meterreading, db)

    db_user = MeterReadingDB(
        # uuid
        uuid=meterreading.uuid,
        # user
        user_id=meterreading.user_id,
        # attachment
        attachment_id=meterreading.attachment_id,
        # customer
        customer_id=meterreading.customer_id,
        # details
        read_date=meterreading.read_date,
        current=meterreading.current,
        previous=meterreading.previous,
        consumption_m3=meterreading.consumption_m3,
        consumption_days=meterreading.consumption_days,
        consumption_zmw=meterreading.consumption_zmw,
        consumption_daily=meterreading.consumption_daily,
        comments=meterreading.comments,
        # status
        access_status=meterreading.access_status,
        reading_status=meterreading.reading_status,
        condition_status=meterreading.condition_status,
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


async def update_meterreading(
    meterreading_id: int, meterreading_update: MeterReading, db: AsyncSession
):
    result = await db.execute(
        select(MeterReadingDB)
        .options(noload("*"))
        .where(MeterReadingDB.id == meterreading_id)
    )
    reading = result.scalar_one_or_none()

    if not reading:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find meterreading with id '{meterreading_id}'",
        )
    # look for consumption
    meterreading_update = await get_consumption_zmw(meterreading_update, db)

    # Update fields that are not None
    for key, value in meterreading_update.dict(exclude_unset=True).items():
        setattr(reading, key, value)

    try:
        await db.commit()
        await db.refresh(reading)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update meterreading {e}"
        )
    return reading


@router.post("/upload", response_model=MeterReading)
async def upload_meterreading(
    meterreading: MeterReading, db: AsyncSession = Depends(get_lwsc_db)
):
    # check if reading with same uuid exists
    result = await db.execute(
        select(MeterReadingDB)
        .options(noload("*"))
        .where(MeterReadingDB.uuid == meterreading.uuid)
    )
    existing = result.scalars().first()
    if existing:
        # update existing record instead of creating new one
        return await update_meterreading(existing.id, meterreading, db)
    else:
        # create new record
        return await create_meterreading(meterreading, db)


@router.post("/create", response_model=MeterReading)
async def create_new(
    meterreading: MeterReading, db: AsyncSession = Depends(get_lwsc_db)
):
    # check if reading with same uuid exists
    return await create_meterreading(meterreading, db)


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    # get all meters
    result = await db.execute(select(CustomerDB))
    customers = result.scalars().all()

    # get current date
    now = assist.get_current_date(False)

    index = 1
    nocustomers = 1

    # for each meter, add readings for all months
    for customer in customers:

        nocustomers += 1

        if nocustomers > 10:
            break

        # get bill rates
        result = await db.execute(
            select(BillRateDB).where(BillRateDB.cat_id == customer.cat_id)
        )
        rates = result.scalars().all()

        # add a reading from 2026
        for y in range(2025, 2027):
            for k in range(1, 13):

                # readings should now exeed current date
                read_date = assist.get_custom_date_tz(y, k, 15, 10, 0)

                if read_date < now:

                    previousReading = round(random.uniform(2.0, 9.0), 2) + (index * 10)
                    currentReading = round(random.uniform(18.0, 30.0), 2) + (index * 10)
                    consumptionM3 = round(currentReading - previousReading, 2)
                    consumptionDays = random.randint(15, 28)
                    consumptionDaily = round(consumptionM3 / consumptionDays, 2)
                    consumptionZMW = lwscapp.get_consumption_rate(consumptionM3, rates)

                    db_status = MeterReadingDB(
                        # uuid
                        uuid=uuid4().hex,
                        # user
                        user_id=customer.user_id,
                        # attachment
                        attachment_id=None,
                        # customer
                        customer_id=customer.id,
                        # details
                        read_date=read_date,
                        current=currentReading,
                        previous=previousReading,
                        consumption_m3=consumptionM3,
                        consumption_days=consumptionDays,
                        consumption_zmw=consumptionZMW,
                        consumption_daily=consumptionDaily,
                        comments="Generated",
                        # status
                        access_status="Accessible",
                        reading_status="Normal",
                        condition_status="OK",
                        # addres
                        lon=random.uniform(10.0, 11.0),
                        lat=random.uniform(10.0, 11.0),
                        # approval
                        status_id=lwscapp.STATUS_APPROVED,
                        stage_id=lwscapp.APPROVAL_STAGE_APPROVED,
                        approval_levels=2,
                        # service
                        created_by="system",
                    )
                    db.add(db_status)
                    index += 1

    try:
        await db.commit()
        # await db.refresh(db_status)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to initialize meter readings: f{e}"
        )
    return {
        "succeeded": True,
        "message": f"{index} Meter readings have been successfully initialized",
    }


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
        select(MeterReadingDB)
        .options(
            selectinload(MeterReadingDB.user),
            selectinload(MeterReadingDB.customer),
            selectinload(MeterReadingDB.attachment),
            selectinload(MeterReadingDB.stage),
            selectinload(MeterReadingDB.status),
        )
        .where(MeterReadingDB.id == meterreading_id)
    )
    reading = result.scalars().first()
    if not reading:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find meterreading with id '{meterreading_id}'",
        )
    return reading


@router.get("/list", response_model=List[MeterReadingWithDetail])
async def list_meterreadings(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(MeterReadingDB)
        .options(
            selectinload(MeterReadingDB.user),
            selectinload(MeterReadingDB.customer),
            selectinload(MeterReadingDB.attachment),
            selectinload(MeterReadingDB.stage),
            selectinload(MeterReadingDB.status),
        )
        .order_by(desc(MeterReadingDB.id))
    )
    return result.scalars().all()
