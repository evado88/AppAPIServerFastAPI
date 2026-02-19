from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.test_reagent_model import TestReagent, TestReagentDB, TestReagentWithDetail
from apps.ccl.models.user_model import UserDB

router = APIRouter(prefix="/testreagents", tags=["TestReagents"])


@router.post("/create", response_model=TestReagentWithDetail)
async def create(testreagent: TestReagent, db: AsyncSession = Depends(get_ccl_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == testreagent.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{testreagent.user_id}' does not exist",
        )

    db_user = TestReagentDB(
        # user
        user_id=testreagent.user_id,
        # details
        test_id=testreagent.test_id,
        reagent_id=testreagent.reagent_id,
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
            status_code=400, detail=f"Unable to create testreagent: f{e}"
        )
    return db_user


@router.get("/id/{testreagent_id}", response_model=TestReagentWithDetail)
async def get_item(testreagent_id: int, db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(TestReagentDB).filter(TestReagentDB.id == testreagent_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find testreagent with id '{testreagent_id}'",
        )
    return category


@router.put("/update/{testreagent_id}", response_model=TestReagentWithDetail)
async def update_item(
    testreagent_id: int,
    testreagent_update: TestReagent,
    db: AsyncSession = Depends(get_ccl_db),
):
    result = await db.execute(
        select(TestReagentDB).where(TestReagentDB.id == testreagent_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find testreagent with id '{testreagent_id}'",
        )

    # Update fields that are not None
    for key, value in testreagent_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update testreagent {e}")
    return config


@router.get("/list", response_model=List[TestReagentWithDetail])
async def list_items(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(TestReagentDB))
    return result.scalars().all()
