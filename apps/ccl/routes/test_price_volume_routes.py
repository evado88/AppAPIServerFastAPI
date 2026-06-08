from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy.orm import selectinload
from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.param_models import ParamDataImport
from apps.ccl.models.test_price_Volume_model import (
    TestPriceVolme,
    TestPriceVolmeDB,
    TestPriceVolmeWithDetail,
)
from apps.ccl.models.user_model import UserDB
from helpers import assist

router = APIRouter(prefix="/test-price-volmes", tags=["TestPriceVolmes"])


@router.post("/create", response_model=TestPriceVolmeWithDetail)
async def create_item(
    testpricevolme: TestPriceVolme, db: AsyncSession = Depends(get_ccl_db)
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == testpricevolme.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{testpricevolme.user_id}' does not exist",
        )

    db_user = TestPriceVolmeDB(
        # user
        user_id=testpricevolme.user_id,
        # details
        name=testpricevolme.name,
        description=testpricevolme.description,
        # period
        month_id=testpricevolme.month,
        year=testpricevolme.year,
        # price volumes
        volume=testpricevolme.volume,
        price=testpricevolme.price,
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
            status_code=400, detail=f"Unable to create test price volme: f{e}"
        )
    return db_user


@router.post("/import")
async def import_customers(
    dataImport: ParamDataImport,
    db: AsyncSession = Depends(get_ccl_db),
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == dataImport.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{dataImport.user_id}' does not exist",
        )

    # existig testpricevolmes
    result = await db.execute(select(TestPriceVolmeDB))

    existingItems = result.scalars().all()

    index = 0
    added = 0
    updated = 0

    startProcess = assist.get_current_date(False)

    for item in dataImport.items:

        # update count
        index += 1

        # get name
        name = item["name"]

        # keep track of items that exist
        itemRecord = next((c for c in existingItems if c.name == name), None)
        itemExists = itemRecord is not None

        if itemExists:

            # update avaitestpricevolmele fields
            for key in item.keys():
                if not key == "no" and not key == "month_name":
                    setattr(itemRecord, key, item[key])

            # commit
            try:
                await db.commit()
                await db.refresh(itemRecord)

                updated += 1
            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Unable to update test price volme: {e}"
                )
        else:
            # add new item
            data = {
                key: item[key]
                for key in item.keys()
                if not key == "no" and not key == "month_name"
            }

            db_customer = TestPriceVolmeDB(
                # user
                user_id=user.id,
                # service
                created_by=user.email,
                **data,
            )
            db.add(db_customer)
            added += 1

    # commit changes
    try:
        # comit changes
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to import test price volmes: f{e}"
        )

    endProcess = assist.get_current_date(False)

    print(f"Import Test Price Volme Duration. Start={startProcess}, End={endProcess}")

    return {
        "succeeded": True,
        "message": f"Successfully imported {index} test price volme(s). Updated {updated} and added {added} test price volme(s)",
    }


@router.get("/id/{id}", response_model=TestPriceVolmeWithDetail)
async def get_item(id: int, db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(TestPriceVolmeDB)
        .options(
            selectinload(TestPriceVolmeDB.user),
            selectinload(TestPriceVolmeDB.month),
        )
        .where(TestPriceVolmeDB.id == id)
        .order_by(TestPriceVolmeDB.name)
    )

    testpricevolme = result.scalars().first()
    if not testpricevolme:
        raise HTTPException(
            status_code=404, detail=f"Unable to find test price volme with id '{id}'"
        )
    return testpricevolme


@router.put("/update/{id}", response_model=TestPriceVolmeWithDetail)
async def update_item(
    id: int,
    testpricevolme_update: TestPriceVolme,
    db: AsyncSession = Depends(get_ccl_db),
):
    result = await db.execute(
        select(TestPriceVolmeDB)
        .options(
            selectinload(TestPriceVolmeDB.user),
            selectinload(TestPriceVolmeDB.month),
        )
        .where(TestPriceVolmeDB.id == id)
        .order_by(TestPriceVolmeDB.name)
    )

    testpricevolme = result.scalar_one_or_none()

    if not testpricevolme:
        raise HTTPException(
            status_code=404, detail=f"Unable to find test price volme with id '{id}'"
        )

    # Update fields that are not None
    for key, value in testpricevolme_update.dict(exclude_unset=True).items():
        setattr(testpricevolme, key, value)

    try:
        await db.commit()
        await db.refresh(testpricevolme)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update test price volme {e}"
        )
    return testpricevolme


@router.get("/list", response_model=List[TestPriceVolmeWithDetail])
async def list(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(TestPriceVolmeDB)
        .options(
            selectinload(TestPriceVolmeDB.user),
            selectinload(TestPriceVolmeDB.month),
        )
        .order_by(TestPriceVolmeDB.name)
    )
    return result.scalars().all()