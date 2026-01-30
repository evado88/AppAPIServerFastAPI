from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from helpers import assist
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.customer_model import CustomerDB
from apps.lwsc.models.meter_model import Meter, MeterDB, MeterWithDetail, MeterWithSimpleDetail
from apps.lwsc.models.user_model import UserDB

router = APIRouter(prefix="/meters", tags=["Meters"])


@router.post("/create", response_model=MeterWithDetail)
async def create_type(meter: Meter, db: AsyncSession = Depends(get_lwsc_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == meter.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{meter.user_id}' does not exist"
        )
        
    db_user = MeterDB(
       # user
        user_id=meter.user_id,
        # town
        town_id=meter.town_id,
        # customer
        customer_id=meter.customer_id,
        # route
        route_id=meter.route_id,
        # personal details
        number=meter.number,
        name=meter.name,
        description=meter.description,
        # contact, address
        lat = meter.lat,
        lon = meter.lon,
        # approval
        status_id=meter.status_id,
        stage_id=meter.stage_id,
        approval_levels=meter.approval_levels,
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
            status_code=400, detail=f"Unable to create meter: f{e}"
        )
    return db_user

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    # get all routes
    result = await db.execute(select(CustomerDB))
    customers = result.scalars().all()

    #add a meter for each customer
    index = 1
    for customer in customers:
        pad = str(index).zfill(3)
        db_status = MeterDB(
            # user
            user_id=customer.user_id,
            # town
            town_id=customer.town_id,
            # customer
            customer_id=customer.id,
            # route
            route_id=customer.route_id,
            # personal details
            number=f'C{customer.id}M1-{pad}',
            name=f'Meter{pad}',
            description=f'Meter for customer {customer.id}',
            # contact, address
            lat = customer.lat,
            lon = customer.lon,
            # approval
            status_id=assist.STATUS_APPROVED,
            stage_id=assist.APPROVAL_STAGE_APPROVED,
            approval_levels=2,
            # service
            created_by="user-001@hotmail.com",
        )
        db.add(db_status)
        index += 1

    try:
        await db.commit()
        # await db.refresh(db_status)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to initialize meters: f{e}"
        )
    return {
        "succeeded": True,
        "message": "Meters have been successfully initialized",
    }


@router.get("/id/{meter_id}", response_model=MeterWithDetail)
async def get_knowledgebase_category(meter_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(MeterDB)
        .filter(MeterDB.id == meter_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Unable to find meter with id '{meter_id}'")
    return category


@router.put("/update/{meter_id}", response_model=MeterWithDetail)
async def update_category(meter_id: int, meter_update: Meter, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(MeterDB)
        .where(MeterDB.id == meter_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Unable to find meter with id '{meter_id}'")
    
    # Update fields that are not None
    for key, value in meter_update.dict(exclude_unset=True).items():
        setattr(config, key, value)
        
    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update meter {e}")
    return config

@router.get("/list", response_model=List[MeterWithDetail])
async def list_meters(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(MeterDB))
    return result.scalars().all()


@router.get("/route/{route_id}", response_model=List[MeterWithDetail])
async def list_route_meters(route_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(MeterDB)
        .filter(MeterDB.route_id == route_id)
    )
    return result.scalars().all()

@router.get("/items", response_model=List[MeterWithSimpleDetail])
async def list_meters_simple(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(MeterDB))
    return result.scalars().all()

