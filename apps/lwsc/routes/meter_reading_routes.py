from datetime import date, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy import desc
from sqlalchemy.orm import selectinload, noload
from apps.lwsc import lwscapp
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.attachment_model import AttachmentDB
from apps.lwsc.models.bill_rate_model import BillRateDB
from apps.lwsc.models.bill_period_model import BillPeriodDB
from apps.lwsc.models.customer_model import CustomerDB
from apps.lwsc.models.district_model import DistrictDB
from apps.lwsc.models.meter_reading_model import (
    MeterReading,
    MeterReadingDB,
    MeterReadingWithDetail,
)
from apps.lwsc.models.param_models import ParamReadingInitialize, ParamUploadTaskResult
from apps.lwsc.models.review_model import AppReview
from apps.lwsc.models.reader_walkroute_model import MeterReaderWalkRouteDB
from apps.lwsc.models.user_model import UserDB
from apps.lwsc.models.walkroute_model import WalkRouteDB
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
        .where(
            MeterReadingDB.uuid != meterreading.uuid,
            MeterReadingDB.customer_id == meterreading.customer_id,
            MeterReadingDB.status_id == assist.STATUS_APPROVED,
        )
        .order_by(desc(MeterReadingDB.read_date))
        .limit(2)
    )
    previousReading = result.scalars().first()

    previousReadingValue  = 0
    
    # if previosu reading exists, use it else use value on customer file
    if previousReading:
        # previous exists
        previousReadingValue  = previousReading.current
    else:
        # no previous, use value on file
        previousReadingValue  = customer.current
    

    previousReadingValue = previousReadingValue if previousReadingValue is not None else 0  
    
    # a reading that has only been raised has no current value yet
    currentReadingValue = meterreading.current if meterreading.current is not None else 0
        
    # reading available. calculate consumption
    consumptionM3 = currentReadingValue - previousReadingValue 
    consumptionZMW = lwscapp.get_consumption_rate(consumptionM3, rates)

    # update valeus for current
    meterreading.previous = previousReadingValue 
    meterreading.consumption_m3 = consumptionM3
    meterreading.consumption_zmw = consumptionZMW

    return meterreading


async def create_meterreading(meterreading: MeterReading, db: AsyncSession):
    # check user exists
    result = await db.execute(
        select(UserDB).where(UserDB.email == meterreading.created_by)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with email '{meterreading.created_by}' does not exist",
        )

    # look for consumption
    meterreading = await get_consumption_zmw(meterreading, db)

    db_reading = MeterReadingDB(
        # period
        period_date=meterreading.period_date,
        # uuid
        uuid=meterreading.uuid,
        # user
        user_id=user.id,
        # attachment
        attachment_id=meterreading.attachment_id,
        # customer
        customer_id=meterreading.customer_id,
        # route and district
        route_name = meterreading.route_name,
        district_name = meterreading.district_name,
        # details
        read_date=meterreading.read_date,
        upload_at=meterreading.upload_at,
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
        updated_at=meterreading.updated_at,
        created_by=user.email,
    )
    db.add(db_reading)
    try:
        await db.commit()
        await db.refresh(db_reading)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to create meterreading: f{e}"
        )

    res = ParamUploadTaskResult(
        succeeded=True,
        approved=False,
        message="The meter reading has been successfully submitted",
        meterreading=db_reading,
    )
    return res
    return db_reading


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
            detail=f"Unable to find meter-reading with id '{meterreading_id}'",
        )

    # check if this has already been approved
    if reading.status_id == lwscapp.STATUS_APPROVED:
        imgUrl = ""

        # check if has attachment
        if reading.attachment_id != 0:
            # attachment specified, load
            result = await db.execute(
                select(AttachmentDB).where(AttachmentDB.id == reading.attachment_id)
            )
            attachment = result.scalars().first()

            # check if exists
            if attachment:
                imgUrl = attachment.path

        return ParamUploadTaskResult(
            succeeded=False,
            approved=True,
            imageUrl=imgUrl,
            message="The meter reading submission has been approved and cannot be updated. Changes reverted",
            meterreading=reading,
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
    res = ParamUploadTaskResult(
        succeeded=True,
        approved=False,
        message="The meter reading submission has been successfully updated",
        meterreading=reading,
    )

    return res


@router.post("/upload", response_model=ParamUploadTaskResult)
async def upload_meterreading(
    meterreading: MeterReading, db: AsyncSession = Depends(get_lwsc_db)
):
    # check if same customer has same reading in period
    # do not use uuid which can change when app is reinstalled
    result = await db.execute(
        select(MeterReadingDB)
        .options(noload("*"))
        .where(
            MeterReadingDB.customer_id == meterreading.customer_id,
            MeterReadingDB.period_date == meterreading.period_date,
        )
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


@router.post("/initialize-reader")
async def initialize_reader_readings(
    readingInit: ParamReadingInitialize, db: AsyncSession = Depends(get_lwsc_db)
):
    """
    Creates placeholder readings for every customer on the routes assigned to
    this meter reader so management can track which readings are still awaiting
    submission for the period.
    """

    # check the meter reader exists
    result = await db.execute(
        select(UserDB).options(noload("*")).where(UserDB.id == readingInit.user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{readingInit.user_id}' does not exist",
        )

    # the period has to be open before a reader can start it on their device
    result = await db.execute(
        select(BillPeriodDB).where(
            BillPeriodDB.year == readingInit.period_date.year,
            BillPeriodDB.month == readingInit.period_date.month,
        )
    )

    period = result.scalars().first()

    if not period:
        raise HTTPException(
            status_code=400,
            detail=(
                f"The billing period for {readingInit.period_date.strftime('%B %Y')} "
                "has not been set up. Please contact the administrator"
            ),
        )

    if not period.is_open:
        raise HTTPException(
            status_code=400,
            detail=(
                f"The billing period '{period.name}' is closed. Please contact "
                "the administrator to have it opened"
            ),
        )

    # get the routes assigned to this reader. Route and district names are
    # stored on the reading itself so the record keeps the route it was
    # raised against even if the customer is moved later
    result = await db.execute(
        select(
            WalkRouteDB.id,
            WalkRouteDB.name,
            DistrictDB.name,
        )
        .select_from(MeterReaderWalkRouteDB)
        .join(WalkRouteDB, WalkRouteDB.id == MeterReaderWalkRouteDB.route_id)
        .join(DistrictDB, DistrictDB.id == WalkRouteDB.district_id)
        .where(MeterReaderWalkRouteDB.user_id == readingInit.user_id)
    )

    assignedRoutes = {
        route_id: {"route": route_name, "district": district_name}
        for route_id, route_name, district_name in result.all()
    }

    if not assignedRoutes:
        # nothing assigned, nothing to raise
        return {
            "succeeded": True,
            "message": f"The meter reader '{user.email}' has no walk routes assigned",
        }

    # get all customers sitting on those routes
    result = await db.execute(
        select(CustomerDB)
        .options(noload("*"))
        .where(CustomerDB.route_id.in_(assignedRoutes.keys()))
    )
    customers = result.scalars().all()

    # find customers that already have a reading for this period so the
    # endpoint can be run more than once without duplicating records
    result = await db.execute(
        select(MeterReadingDB.customer_id).where(
            MeterReadingDB.period_date == readingInit.period_date,
            MeterReadingDB.customer_id.in_([obj.id for obj in customers]),
        )
    )
    existingReadings = {row[0] for row in result.all()}

    # the period date is used as the placeholder read date. The record is
    # marked as awaiting so it is not mistaken for an actual reading
    placeholderDate = assist.get_date_tz(
        datetime(
            readingInit.period_date.year,
            readingInit.period_date.month,
            readingInit.period_date.day,
        )
    )

    added = 0
    skipped = 0

    for customer in customers:
        # skip customers that have already been read for this period
        if customer.id in existingReadings:
            skipped += 1
            continue

        route = assignedRoutes[customer.route_id]

        db_reading = MeterReadingDB(
            # period
            period_date=readingInit.period_date,
            # uuid
            uuid=uuid4().hex,
            # user
            user_id=readingInit.user_id,
            # customer
            customer_id=customer.id,
            # route and district
            route_name=route["route"],
            district_name=route["district"],
            # attachment
            attachment_id=None,
            # details
            read_date=placeholderDate,
            upload_at=None,
            current=None,
            previous=customer.current if customer.current is not None else 0,
            consumption_m3=None,
            consumption_days=None,
            consumption_zmw=None,
            consumption_daily=None,
            comments=None,
            # status
            access_status=lwscapp.READING_AWAITING,
            reading_status=lwscapp.READING_AWAITING,
            condition_status=lwscapp.READING_AWAITING,
            # address
            lat=None,
            lon=None,
            # approval
            status_id=lwscapp.STATUS_DRAFT,
            stage_id=lwscapp.APPROVAL_AWAITING_SUBMISSION,
            approval_levels=2,
            # service
            created_by=user.email,
        )
        db.add(db_reading)
        added += 1

    # commit changes
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Unable to initialize meter readings for the meter reader: f{e}",
        )

    return {
        "succeeded": True,
        "message": (
            f"{added} meter reading(s) awaiting submission have been initialized for "
            f"{user.email} across {len(assignedRoutes)} route(s). "
            f"Skipped {skipped} customer(s) already read for this period"
        ),
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


@router.get("/reader/{user_id}/{year}/{month}", response_model=List[MeterReading])
async def list_reader_meterreadings(
    user_id: int, year: int, month: int, db: AsyncSession = Depends(get_lwsc_db)
):
    """
    Returns the readings this meter reader has already submitted for the period
    whatever their approval status. The mobile app uses this to restore the
    work a reader has already done when the readings for a period are raised
    on the device again.
    """

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400, detail=f"The month '{month}' is not a valid month"
        )

    # check the meter reader exists
    result = await db.execute(
        select(UserDB).options(noload("*")).where(UserDB.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{user_id}' does not exist"
        )

    # work out the period range. Readings are filtered on a range rather than an
    # exact date because a submitted reading can carry any day in the month
    periodStart = date(year, month, 1)
    periodEnd = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    # only the readings that have actually been taken are returned. A reading
    # that has only been raised has no current value on it yet
    result = await db.execute(
        select(MeterReadingDB)
        .options(noload("*"))
        .where(
            MeterReadingDB.user_id == user_id,
            MeterReadingDB.period_date >= periodStart,
            MeterReadingDB.period_date < periodEnd,
            MeterReadingDB.current.is_not(None),
        )
        .order_by(MeterReadingDB.customer_id)
    )

    return result.scalars().all()


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


@router.put("/review-update/{id}", response_model=MeterReading)
async def review_posting(
    id: int, review: AppReview, db: AsyncSession = Depends(get_lwsc_db)
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
    result = await db.execute(select(MeterReadingDB).where(MeterReadingDB.id == id))
    reading = result.scalar_one_or_none()

    if not reading:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find meter reading with specified id '{id}'",
        )

    if reading.status_id == lwscapp.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The meter reading with id '{id}' has already been approved",
        )

    reading.updated_by = user.email

    approveMeeting = False

    if reading.stage_id == lwscapp.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        if reading.created_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the primary reviewer of a meter reading you created",
            )

        reading.review1_at = assist.get_current_date(False)
        reading.review1_by = user.email
        reading.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            reading.status_id = lwscapp.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if reading.approval_levels == 1:
                # one level, no furthur stage approvers

                # approve announcement
                approveMeeting = True

            elif reading.approval_levels == 2 or reading.approval_levels == 3:
                # two or three levels, move to primary
                reading.stage_id = lwscapp.APPROVAL_STAGE_PRIMARY_REVIEW

    elif reading.stage_id == lwscapp.APPROVAL_STAGE_PRIMARY_REVIEW:
        # primary stage

        if reading.review1_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the secondary reviewer since you were the primary reviewer",
            )

        reading.review2_at = assist.get_current_date(False)
        reading.review2_by = user.email
        reading.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            reading.status_id = lwscapp.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if reading.approval_levels == 2:
                # two levels, no furthur stage approvers

                approveMeeting = True

            elif reading.approval_levels == 3:
                # three levels, move to secondary
                reading.stage_id = lwscapp.APPROVAL_STAGE_SECONDARY_REVIEW

    elif reading.stage_id == lwscapp.APPROVAL_STAGE_SECONDARY_REVIEW:
        # secondary stage

        if reading.review2_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the final reviewer since you were the secondary reviewer",
            )

        reading.review3_at = assist.get_current_date(False)
        reading.review3_by = user.email
        reading.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            reading.status_id = lwscapp.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage
            approveMeeting = True

    if approveMeeting:
        # change announcement status
        reading.status_id = lwscapp.STATUS_APPROVED
        reading.stage_id = lwscapp.APPROVAL_STAGE_APPROVED

    try:
        await db.commit()
        await db.refresh(reading)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update meter reading: {e}"
        )
    return reading
