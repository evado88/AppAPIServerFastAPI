from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.test_instrument_model import TestInstrument, TestInstrumentDB, TestInstrumentWithDetail
from apps.ccl.models.user_model import UserDB

router = APIRouter(prefix="/testinstruments", tags=["TestInstruments"])


@router.post("/create", response_model=TestInstrumentWithDetail)
async def create(testinstrument: TestInstrument, db: AsyncSession = Depends(get_ccl_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == testinstrument.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{testinstrument.user_id}' does not exist",
        )

    db_user = TestInstrumentDB(
        # user
        user_id=testinstrument.user_id,
        # details
        test_id=testinstrument.test_id,
        instrument_id=testinstrument.instrument_id,
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
            status_code=400, detail=f"Unable to create testinstrument: f{e}"
        )
    return db_user


@router.get("/id/{testinstrument_id}", response_model=TestInstrumentWithDetail)
async def get_item(testinstrument_id: int, db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(TestInstrumentDB).filter(TestInstrumentDB.id == testinstrument_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find testinstrument with id '{testinstrument_id}'",
        )
    return category


@router.put("/update/{testinstrument_id}", response_model=TestInstrumentWithDetail)
async def update_item(
    testinstrument_id: int,
    testinstrument_update: TestInstrument,
    db: AsyncSession = Depends(get_ccl_db),
):
    result = await db.execute(
        select(TestInstrumentDB).where(TestInstrumentDB.id == testinstrument_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find testinstrument with id '{testinstrument_id}'",
        )

    # Update fields that are not None
    for key, value in testinstrument_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update testinstrument {e}")
    return config


@router.get("/list", response_model=List[TestInstrumentWithDetail])
async def list_items(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(TestInstrumentDB))
    return result.scalars().all()
