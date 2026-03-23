from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.district_model import District, DistrictDB, DistrictSimple, DistrictWithDetail
from apps.lwsc.models.user_model import UserDB
from apps.lwsc import lwscapp

router = APIRouter(prefix="/districts", tags=["Districts"])


@router.post("/create", response_model=DistrictWithDetail)
async def post_district(district: District, db: AsyncSession = Depends(get_lwsc_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == district.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id {district.user_id} does not exist",
        )

    db_tran = DistrictDB(
        # user
        user_id=district.user_id,
        # transaction
        name=district.name,
        code=district.code,
        description=district.description,
        # approval
        status_id=district.status_id,
        stage_id=district.stage_id,
        approval_levels=district.approval_levels,
        # service
        created_by=user.email,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create district: {e}")
    return db_tran


@router.put("/update/{district_id}", response_model=DistrictWithDetail)
async def update_district(
    district_id: int, district_update: District, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(select(DistrictDB).where(DistrictDB.id == district_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"Unable to find district with id '{district_id}'"
        )

    # Update fields that are not None
    for key, value in district_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update district {e}")
    return config


@router.get("/list", response_model=List[DistrictWithDetail])
async def list__districts(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(DistrictDB))
    queries = result.scalars().all()
    return queries


@router.get("/items", response_model=List[DistrictSimple])
async def list__districts(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(DistrictDB))
    queries = result.scalars().all()
    return queries


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):

    districts = [
        {"name": "Samfya", "code": "SAM"},
        {"name": "Mansa", "code": "MSA"},
        {"name": "Mwense", "code": "MWE"},
    ]

    for district in districts:
        db_status = DistrictDB(
            # personal details
            user_id=1,
            name=district['name'],
            code=district['code'],
            # approval
            status_id=lwscapp.STATUS_APPROVED,
            stage_id=lwscapp.APPROVAL_STAGE_APPROVED,
            approval_levels=2,
        )
        db.add(db_status)

    try:
        await db.commit()
        # await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to initialize districts: f{e}")
    return {
        "succeeded": True,
        "message": "Districts have been successfully initialized",
    }


@router.get("/id/{district_id}", response_model=DistrictWithDetail)
async def get__district(district_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(DistrictDB).filter(DistrictDB.id == district_id))
    district = result.scalars().first()
    if not district:
        raise HTTPException(
            status_code=404, detail=f"Unable to find district with id '{district_id}'"
        )
    return district
