from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy.orm import selectinload
from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.instrument_model import (
    Instrument,
    InstrumentDB,
    InstrumentItem,
    InstrumentParam,
    InstrumentWithDetail,
)
from apps.ccl.models.lab_model import LabDB
from apps.ccl.models.user_model import UserDB

router = APIRouter(prefix="/instruments", tags=["Instruments"])


@router.post("/create", response_model=InstrumentWithDetail)
async def create_item(instrument: Instrument, db: AsyncSession = Depends(get_ccl_db)):
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
        serial_no=instrument.serial_no,
        description=instrument.description,
        
        # costs
        cost=instrument.cost,
        amortization=instrument.amortization,
        annual_cost=instrument.annual_cost,
        maintenance_cost=instrument.maintenance_cost,
        total_cost=instrument.total_cost,
        
        # calibration
        calibration_cycle =instrument.calibration_cycle,
        calibration_kit_cost = instrument.calibration_kit_cost,
        calibration_service_cost = instrument.calibration_service_cost,
        calibration_annual_cost = instrument.calibration_annual_cost, 
          
        # lists
        lab_list=instrument.lab_list,
        
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


@router.get("/id/{instrument_id}", response_model=InstrumentParam)
async def get_item(instrument_id: int, db: AsyncSession = Depends(get_ccl_db)):
    
    # only get if not zero
    instrumentItem = None
    if instrument_id != 0:
        result = await db.execute(
            select(InstrumentDB)
            .options(
                selectinload(InstrumentDB.user),
            )
            .where(InstrumentDB.id == instrument_id)
        )

        instrumentItem = result.scalars().first()
        if not instrumentItem:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to find instrument with id '{instrument_id}'",
            )
            
    # get labs
    result = await db.execute(
        select(LabDB)
        .options(
            selectinload(LabDB.user),
        )
        .order_by(LabDB.name)
    )
    labList = result.scalars().all()
    
    # return param
    param = InstrumentParam(instrument=instrumentItem, labs=labList)
    
    return param



@router.put("/update/{instrument_id}", response_model=InstrumentWithDetail)
async def update_item(
    instrument_id: int,
    instrument_update: Instrument,
    db: AsyncSession = Depends(get_ccl_db),
):
    result = await db.execute(
        select(InstrumentDB)
        .options(
            selectinload(InstrumentDB.user),
        )
        .where(InstrumentDB.id == instrument_id)
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
async def list(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(InstrumentDB)
        .options(
            selectinload(InstrumentDB.user),
        )
        .order_by(InstrumentDB.name)
    )
    return result.scalars().all()


@router.get("/items", response_model=List[InstrumentItem])
async def list_items(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(InstrumentDB)
        .options(
            selectinload(InstrumentDB.user),
        )
        .order_by(InstrumentDB.name)
    )
    return result.scalars().all()

