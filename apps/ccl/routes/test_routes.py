from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.instrument_model import InstrumentDB
from apps.ccl.models.instrument_model import InstrumentDB
from apps.ccl.models.lab_model import LabDB
from apps.ccl.models.param_models import ParamTestDetail
from apps.ccl.models.reagent_model import ReagentDB
from apps.ccl.models.test_model import Test, TestDB, TestWithDetail
from apps.ccl.models.user_model import UserDB

router = APIRouter(prefix="/tests", tags=["Tests"])


@router.post("/create", response_model=TestWithDetail)
async def create(test: Test, db: AsyncSession = Depends(get_ccl_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == test.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{test.user_id}' does not exist"
        )

    db_user = TestDB(
        # user
        user_id=test.user_id,
        # details
        name=test.name,
        description=test.description,
        # annual volumnes
        annual_credit=test.annual_credit,
        annual_nhima=test.annual_nhima,
        annual_research=test.annual_research,
        annual_walkins=test.annual_walkins,
        # totals
        annual_shift=test.annual_shift,
        annual_total=test.annual_total,
        # lab plans
        sites_no=test.sites_no,
        staff_no=test.staff_no,
        # instrument usage
        runs_day_week=test.runs_day_week,
        runs_shift_day=test.runs_shift_day,
        runs_annual=test.runs_annual,
        runs_average_volume=test.runs_average_volume,
        # lists
        reagent_list=test.reagent_list,
        instrument_list=test.instrument_list,
        # service
        created_by=user.email,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create test: f{e}")
    return db_user


@router.get("/id/{test_id}", response_model=TestWithDetail)
async def get_item(test_id: int, db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(TestDB).filter(TestDB.id == test_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404, detail=f"Unable to find test with id '{test_id}'"
        )
    return category


@router.get("/detail/{test_id}", response_model=ParamTestDetail)
async def get_test_detail(test_id: int, db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(InstrumentDB))
    instruments = result.scalars().all()

    result = await db.execute(select(ReagentDB))
    reagents = result.scalars().all()

    result = await db.execute(select(LabDB))
    labs = result.scalars().all()

    result = await db.execute(select(TestDB).filter(TestDB.id == test_id))
    test = result.scalars().first()
    if not test:
        raise HTTPException(
            status_code=404, detail=f"Unable to find test with id '{test_id}'"
        )

    return ParamTestDetail(
        labs=labs, reagents=reagents, instruments=instruments, test=test
    )


@router.get("/param", response_model=ParamTestDetail)
async def get_test_pram(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(InstrumentDB))
    instruments = result.scalars().all()

    result = await db.execute(select(ReagentDB))
    reagents = result.scalars().all()

    result = await db.execute(select(LabDB))
    labs = result.scalars().all()

    return ParamTestDetail(
        labs=labs, reagents=reagents, instruments=instruments, test=None
    )


@router.put("/update/{test_id}", response_model=TestWithDetail)
async def update_item(
    test_id: int, test_update: Test, db: AsyncSession = Depends(get_ccl_db)
):
    result = await db.execute(select(TestDB).where(TestDB.id == test_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"Unable to find test with id '{test_id}'"
        )

    # Update fields that are not None
    for key, value in test_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update test {e}")
    return config


@router.get("/list", response_model=List[TestWithDetail])
async def list_items(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(TestDB))
    return result.scalars().all()
