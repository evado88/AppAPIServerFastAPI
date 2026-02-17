from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.meter_status_model import MeterStatus, MeterStatusDB, MeterStatusSimple, MeterStatusWithDetail
from apps.lwsc.models.user_model import UserDB

router = APIRouter(prefix="/meter-statuses", tags=["MeterStatuses"])


@router.post("/create", response_model=MeterStatusWithDetail)
async def post_meter_status(meterstatus: MeterStatus, db: AsyncSession = Depends(get_lwsc_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == meterstatus.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id {meterstatus.user_id} does not exist",
        )

    db_tran = MeterStatusDB(
        # user
        user_id=meterstatus.user_id,
        # transaction
        status_name=meterstatus.status_name,
        status_type=meterstatus.status_type,
        description=meterstatus.description,
        # service
        created_by=user.email,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create meter status: {e}")
    return db_tran


@router.put("/update/{cat_id}", response_model=MeterStatusWithDetail)
async def update_meterstatus(
    cat_id: int, meterstatus_update: MeterStatus, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(select(MeterStatusDB).where(MeterStatusDB.id == cat_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"Unable to find meter status with id '{cat_id}'"
        )

    # Update fields that are not None
    for key, value in meterstatus_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update meter status {e}")
    return config


@router.get("/list", response_model=List[MeterStatusWithDetail])
async def list_meter_statuses(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(MeterStatusDB))
    queries = result.scalars().all()
    return queries

@router.get("/list/simple", response_model=List[MeterStatusSimple])
async def list_meter_statuses_simple(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(MeterStatusDB))
    queries = result.scalars().all()
    return queries

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    typeList = [
        {"name": "Unavailable", "type": "Reading"},
        {"name": "Normal", "type": "Reading"},
        {"name": "Estimated", "type": "Reading"},
        {"name": "Self-Read", "type": "Reading"},
        {"name": "Initial Reading", "type": "Reading"},
        {"name": "Final Reading", "type": "Reading"},
        {"name": "Accessible", "type": "Access"},
        {"name": "No Access", "type": "Access"},
        {"name": "Gate Locked", "type": "Access"},
        {"name": "Dog on Premises", "type": "Access"},
        {"name": "Customer Not Available", "type": "Access"},
        {"name": "Obstructed Meter", "type": "Access"},
        {"name": "OK", "type": "Condition"},
        {"name": "Damaged", "type": "Condition"},
        {"name": "Leaking", "type": "Condition"},
        {"name": "Tampered", "type": "Condition"},
        {"name": "Broken Glass", "type": "Condition"},
        {"name": "Corroded", "type": "Condition"},
        {"name": "Illegible Display", "type": "Condition"},
        {"name": "Stopped / Not Turning", "type": "Condition"},
        {"name": "Running Backwards", "type": "Condition"},
    ]
    typeId = 1

    for value in typeList:
        db_status = MeterStatusDB(
            # personal details
            user_id=1,
            status_name=value["name"],
            status_type=value["type"],
        )
        db.add(db_status)
        typeId += 1

    try:
        await db.commit()
        # await db.refresh(db_status)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to initialize meter statuses: {e}"
        )
    return {
        "succeeded": True,
        "message": "Meter statuses have been successfully initialized",
    }


@router.get("/id/{status_id}", response_model=MeterStatusWithDetail)
async def get_meter_status(status_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(MeterStatusDB).filter(MeterStatusDB.id == status_id))
    meterstatus = result.scalars().first()
    if not meterstatus:
        raise HTTPException(
            status_code=404, detail=f"Unable to find meter status with id '{status_id}'"
        )
    return meterstatus
