from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.town_model import Town, TownDB, TownSimple, TownWithDetail
from apps.lwsc.models.user_model import UserDB
from helpers import assist

router = APIRouter(prefix="/towns", tags=["Towns"])


@router.post("/create", response_model=TownWithDetail)
async def post__town(town: Town, db: AsyncSession = Depends(get_lwsc_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == town.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id {town.user_id} does not exist",
        )

    db_tran = TownDB(
        # user
        user_id=town.user_id,
        # transaction
        name=town.name,
        code=town.code,
        description=town.description,
        # approval
        status_id=town.status_id,
        stage_id=town.stage_id,
        approval_levels=town.approval_levels,
        # service
        created_by=user.email,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create town: {e}")
    return db_tran


@router.put("/update/{cat_id}", response_model=TownWithDetail)
async def update_town(
    cat_id: int, town_update: Town, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(select(TownDB).where(TownDB.id == cat_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"Unable to find town with id '{cat_id}'"
        )

    # Update fields that are not None
    for key, value in town_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update town {e}")
    return config


@router.get("/list", response_model=List[TownWithDetail])
async def list__towns(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(TownDB))
    queries = result.scalars().all()
    return queries

@router.get("/items", response_model=List[TownSimple])
async def list__towns(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(TownDB))
    queries = result.scalars().all()
    return queries


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):

    for i in range(1, 4):
        db_status = TownDB(
            # personal details
            user_id=1,
            name=f'Town {i}',
            code=f'TN{i}',
            # approval
            status_id=assist.STATUS_APPROVED,
            stage_id=assist.APPROVAL_STAGE_APPROVED,
            approval_levels=2,
        )
        db.add(db_status)

    try:
        await db.commit()
        # await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to initialize towns: f{e}")
    return {
        "succeeded": True,
        "message": "Towns have been successfully initialized",
    }


@router.get("/id/{cat_id}", response_model=TownWithDetail)
async def get__town(cat_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(TownDB).filter(TownDB.id == cat_id))
    town = result.scalars().first()
    if not town:
        raise HTTPException(
            status_code=404, detail=f"Unable to find town with id '{cat_id}'"
        )
    return town
