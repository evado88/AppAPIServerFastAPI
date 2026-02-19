from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.instrument_model import Instrument, InstrumentDB, InstrumentWithDetail
from apps.ccl.models.user_model import UserDB

router = APIRouter(prefix="/instruments", tags=["Instruments"])


@router.post("/create", response_model=InstrumentWithDetail)
async def create(instrument: Instrument, db: AsyncSession = Depends(get_ccl_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == instrument.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{instrument.user_id}' does not exist",
        )

    db_user = InstrumentDB(
        # user
        user_id=instrument.user_id,
        # details
        name=instrument.name,
        description=instrument.description,
        #costs
        cost=instrument.cost,
        amortization=instrument.amortization,
        annual_cost=instrument.annual_cost,
        maintenance_cost=instrument.maintenance_cost,
        total_cost = instrument.total_cost,
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
            status_code=400, detail=f"Unable to create instrument: f{e}"
        )
    return db_user


@router.get("/id/{instrument_id}", response_model=InstrumentWithDetail)
async def get_item(instrument_id: int, db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(InstrumentDB).filter(InstrumentDB.id == instrument_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find instrument with id '{instrument_id}'",
        )
    return category


@router.put("/update/{instrument_id}", response_model=InstrumentWithDetail)
async def update_item(
    instrument_id: int,
    instrument_update: Instrument,
    db: AsyncSession = Depends(get_ccl_db),
):
    result = await db.execute(
        select(InstrumentDB).where(InstrumentDB.id == instrument_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find instrument with id '{instrument_id}'",
        )

    # Update fields that are not None
    for key, value in instrument_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update instrument {e}")
    return config


@router.get("/list", response_model=List[InstrumentWithDetail])
async def list_items(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(InstrumentDB))
    return result.scalars().all()
