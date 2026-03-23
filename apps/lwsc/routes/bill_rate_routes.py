from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Any

from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.bill_rate_model import (
    BillRate,
    BillRateDB,
    BillRateWithDetail,
)
from apps.lwsc.models.meter_model import MeterDB
from apps.lwsc.models.user_model import UserDB
from apps.lwsc.models.walkroute_model import WalkRouteDB
from helpers import assist
import random
from apps.lwsc import lwscapp

router = APIRouter(prefix="/bill-rates", tags=["BillRates"])


@router.post("/create", response_model=BillRateWithDetail)
async def create_type(billrate: BillRate, db: AsyncSession = Depends(get_lwsc_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == billrate.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{billrate.user_id}' does not exist",
        )

    db_user = BillRateDB(
        # user
        user_id=billrate.user_id,
        # cat
        cat_id=billrate.cat_id,
        # band
        name=billrate.name,
        order=billrate.order,
        from_vol=billrate.from_vol,
        to_vol=billrate.to_vol,
        rate=billrate.rate,
        # service
        created_by=user.email,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create bill rate: f{e}")
    return db_user



@router.get("/id/{billrate_id}", response_model=BillRateWithDetail)
async def get_knowledgebase_category(
    billrate_id: int, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(select(BillRateDB).filter(BillRateDB.id == billrate_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404, detail=f"Unable to find bill rate with id '{billrate_id}'"
        )
    return category


@router.put("/update/{billrate_id}", response_model=BillRateWithDetail)
async def update_category(
    billrate_id: int, billrate_update: BillRate, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(select(BillRateDB).where(BillRateDB.id == billrate_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"Unable to find billrate with id '{billrate_id}'"
        )

    # Update fields that are not None
    for key, value in billrate_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update billrate {e}")
    return config


@router.get("/list", response_model=List[BillRateWithDetail])
async def list_billrates(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(BillRateDB))
    return result.scalars().all()

@router.get("/items", response_model=List[BillRate])
async def list_billrates_simple(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(BillRateDB))
    return result.scalars().all()