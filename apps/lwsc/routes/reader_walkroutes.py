from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from apps.lwsc.models.district_model import DistrictDB
from apps.lwsc.models.walkroute_model import WalkRouteDB
from helpers import assist
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.reader_walkroute_model import (
    MeterReaderWalkRoute,
    MeterReaderWalkRouteDB,
    MeterReaderWalkRouteWithDetail,
)
from apps.lwsc.models.user_model import UserDB
from sqlalchemy.orm import load_only, noload, selectinload

router = APIRouter(prefix="/reader-walk-routes", tags=["MeterReaderWalkRoutes"])


@router.post("/create", response_model=MeterReaderWalkRoute)
async def create_type(
    route: MeterReaderWalkRoute, db: AsyncSession = Depends(get_lwsc_db)
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == route.user_id))

    existingUser = result.scalars().first()
    if not existingUser:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{route.user_id}' does not exist"
        )

    # check route exists
    result = await db.execute(
        select(WalkRouteDB).where(WalkRouteDB.id == route.route_id)
    )

    existingRoute = result.scalars().first()
    if not existingRoute:
        raise HTTPException(
            status_code=400,
            detail=f"The route with id '{route.route_id}' does not exist",
        )

    db_user = MeterReaderWalkRouteDB(
        # user
        user_id=route.user_id,
        # routre
        route_id=route.route_id,
        # service
        created_by=existingUser.email,
    )

    db.add(db_user)

    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to create reader route: f{e}"
        )
    return db_user


@router.get("/id/{reader_route_id}", response_model=MeterReaderWalkRouteWithDetail)
async def get_knowledgebase_category(
    reader_route_id: int, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(
        select(MeterReaderWalkRouteDB)
        .options(
            selectinload(MeterReaderWalkRouteDB.user),
            selectinload(MeterReaderWalkRouteDB.route).selectinload(
                WalkRouteDB.district
            ),
        )
        .where(MeterReaderWalkRouteDB.id == reader_route_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find reader route with id '{reader_route_id}'",
        )
    return category


@router.put("/update/{reader_route_id}", response_model=MeterReaderWalkRouteWithDetail)
async def update_category(
    reader_route_id: int,
    route_update: MeterReaderWalkRoute,
    db: AsyncSession = Depends(get_lwsc_db),
):
    result = await db.execute(
        select(MeterReaderWalkRouteDB)
        .options(
            selectinload(MeterReaderWalkRouteDB.user),
            selectinload(MeterReaderWalkRouteDB.route).selectinload(
                WalkRouteDB.district
            ),
        )
        .where(MeterReaderWalkRouteDB.id == reader_route_id)
    )

    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find reader route with id '{reader_route_id}'",
        )

    # Update fields that are not None
    for key, value in route_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update reader route {e}"
        )
    return config


@router.get("/list", response_model=List[MeterReaderWalkRouteWithDetail])
async def list_routes(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(MeterReaderWalkRouteDB).options(
            selectinload(MeterReaderWalkRouteDB.user),
            selectinload(MeterReaderWalkRouteDB.route).selectinload(
                WalkRouteDB.district
            ),
        )
    )

    return result.scalars().all()


@router.get("/items", response_model=List[MeterReaderWalkRoute])
async def list_routes(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(MeterReaderWalkRouteDB).options(
            noload("*"),
        )
    )

    return result.scalars().all()
