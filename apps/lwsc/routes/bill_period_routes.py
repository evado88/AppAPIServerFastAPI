import calendar
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy import desc
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.bill_period_model import (
    BillPeriod,
    BillPeriodAction,
    BillPeriodDB,
    BillPeriodItem,
)
from helpers import assist

router = APIRouter(prefix="/bill-periods", tags=["BillPeriods"])

# the periods are created from this year up to and including December 2030
PERIOD_START_YEAR = 2025
PERIOD_END_YEAR = 2030


async def get_period(year: int, month: int, db: AsyncSession):
    """
    Finds the billing period for the given year and month
    """
    result = await db.execute(
        select(BillPeriodDB).where(
            BillPeriodDB.year == year, BillPeriodDB.month == month
        )
    )

    return result.scalars().first()


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    """
    Creates every billing period up to December 2030. Periods are closed until
    management opens them, and periods that already exist are left alone so the
    route can be run again safely.
    """

    # get the periods that have already been created
    result = await db.execute(select(BillPeriodDB.period_date))

    existingPeriods = {row[0] for row in result.all()}

    added = 0
    skipped = 0

    for year in range(PERIOD_START_YEAR, PERIOD_END_YEAR + 1):
        for month in range(1, 13):
            periodDate = date(year, month, 1)

            if periodDate in existingPeriods:
                # already created, leave it as management has set it
                skipped += 1
                continue

            db_period = BillPeriodDB(
                # period
                period_date=periodDate,
                name=f"{calendar.month_name[month]} {year}",
                year=year,
                month=month,
                description=None,
                # a period is closed until it is opened
                is_open=False,
            )

            db.add(db_period)
            added += 1

    # commit changes
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to initialize the billing periods: {e}"
        )

    return {
        "succeeded": True,
        "message": (
            f"{added} billing period(s) have been created up to December "
            f"{PERIOD_END_YEAR}. Skipped {skipped} period(s) that already exist"
        ),
    }


@router.get("/list", response_model=List[BillPeriod])
async def list_periods(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(BillPeriodDB).order_by(desc(BillPeriodDB.period_date))
    )

    return result.scalars().all()


@router.get("/list/open", response_model=List[BillPeriodItem])
async def list_open_periods(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(BillPeriodDB)
        .where(BillPeriodDB.is_open == True)
        .order_by(desc(BillPeriodDB.period_date))
    )

    return result.scalars().all()


@router.get("/id/{period_id}", response_model=BillPeriod)
async def get_period_by_id(period_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(BillPeriodDB).where(BillPeriodDB.id == period_id)
    )

    period = result.scalars().first()

    if not period:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find the billing period with id '{period_id}'",
        )

    return period


@router.get("/period/{year}/{month}", response_model=BillPeriod)
async def get_period_by_date(
    year: int, month: int, db: AsyncSession = Depends(get_lwsc_db)
):
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400, detail=f"The month '{month}' is not a valid month"
        )

    period = await get_period(year, month, db)

    if not period:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find the billing period for {month}/{year}",
        )

    return period


@router.put("/open/{period_id}", response_model=BillPeriod)
async def open_period(
    period_id: int,
    action: BillPeriodAction,
    db: AsyncSession = Depends(get_lwsc_db),
):
    """
    Opens the period so meter readers can start it on their devices
    """
    result = await db.execute(
        select(BillPeriodDB).where(BillPeriodDB.id == period_id)
    )

    period = result.scalars().first()

    if not period:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find the billing period with id '{period_id}'",
        )

    if period.is_open:
        raise HTTPException(
            status_code=400,
            detail=f"The billing period '{period.name}' is already open",
        )

    period.is_open = True
    period.opened_at = assist.get_current_date(False)
    period.opened_by = action.email
    period.updated_by = action.email

    try:
        await db.commit()
        await db.refresh(period)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to open the billing period: {e}"
        )

    return period


@router.put("/close/{period_id}", response_model=BillPeriod)
async def close_period(
    period_id: int,
    action: BillPeriodAction,
    db: AsyncSession = Depends(get_lwsc_db),
):
    """
    Closes the period so meter readers can no longer start it on their devices
    """
    result = await db.execute(
        select(BillPeriodDB).where(BillPeriodDB.id == period_id)
    )

    period = result.scalars().first()

    if not period:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find the billing period with id '{period_id}'",
        )

    if not period.is_open:
        raise HTTPException(
            status_code=400,
            detail=f"The billing period '{period.name}' is already closed",
        )

    period.is_open = False
    period.closed_at = assist.get_current_date(False)
    period.closed_by = action.email
    period.updated_by = action.email

    try:
        await db.commit()
        await db.refresh(period)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to close the billing period: {e}"
        )

    return period


@router.put("/update/{period_id}", response_model=BillPeriod)
async def update_period(
    period_id: int,
    period_update: BillPeriod,
    db: AsyncSession = Depends(get_lwsc_db),
):
    result = await db.execute(
        select(BillPeriodDB).where(BillPeriodDB.id == period_id)
    )

    period = result.scalars().first()

    if not period:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find the billing period with id '{period_id}'",
        )

    # Update fields that are not None
    for key, value in period_update.dict(exclude_unset=True).items():
        setattr(period, key, value)

    try:
        await db.commit()
        await db.refresh(period)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update the billing period {e}"
        )

    return period
