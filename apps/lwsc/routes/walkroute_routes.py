from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from helpers import assist
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.walkroute_model import WalkRoute, WalkRouteDB, WalkRouteSimple, WalkRouteWithDetail, WalkRouteWithSimpleDetail
from apps.lwsc.models.user_model import UserDB

router = APIRouter(prefix="/walk-routes", tags=["WalkRoutes"])


@router.post("/create", response_model=WalkRouteWithDetail)
async def create_type(route: WalkRoute, db: AsyncSession = Depends(get_lwsc_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == route.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{route.user_id}' does not exist"
        )
        
    db_user = WalkRouteDB(
        # user
        user_id=route.user_id,
        # town
        town_id=route.town_id,
        # details
        name=route.name,
        description=route.description,
        # approval
        status_id=route.status_id,
        stage_id=route.stage_id,
        approval_levels=route.approval_levels,
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
            status_code=400, detail=f"Unable to create route: f{e}"
        )
    return db_user

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
 
    for i in range(1, 4):

        for k in range(1, 3):
            db_status = WalkRouteDB(
                # user
                user_id=1,
                # town
                town_id=i,
                # details
                name=f'Town {i} - Route {k}',
                description=f'The route {k} for town {i}',
                # approval
                status_id=assist.STATUS_APPROVED,
                stage_id=assist.APPROVAL_STAGE_APPROVED,
                approval_levels=2,
                # service
                created_by='user-001@hotmail.com',
            )
            db.add(db_status)

    try:
        await db.commit()
        # await db.refresh(db_status)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to initialize walk routes: f{e}")
    return {
        "succeeded": True,
        "message": "Walk routes have been successfully initialized",
    }

@router.get("/id/{route_id}", response_model=WalkRouteWithDetail)
async def get_knowledgebase_category(route_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(WalkRouteDB)
        .filter(WalkRouteDB.id == route_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Unable to find route with id '{route_id}'")
    return category


@router.put("/update/{route_id}", response_model=WalkRouteWithDetail)
async def update_category(route_id: int, route_update: WalkRoute, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(WalkRouteDB)
        .where(WalkRouteDB.id == route_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Unable to find route with id '{route_id}'")
    
    # Update fields that are not None
    for key, value in route_update.dict(exclude_unset=True).items():
        setattr(config, key, value)
        
    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update route {e}")
    return config

@router.get("/list", response_model=List[WalkRouteWithDetail])
async def list_routes(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(WalkRouteDB))
    return result.scalars().all()

@router.get("/items", response_model=List[WalkRouteWithSimpleDetail])
async def list_routes(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(WalkRouteDB))
    return result.scalars().all()