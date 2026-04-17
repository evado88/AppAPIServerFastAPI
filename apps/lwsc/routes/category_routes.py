from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List

from apps.lwsc import lwscapp
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.bill_rate_model import BillRateDB
from apps.lwsc.models.category_model import Category, CategoryDB, CategoryWithDetail
from apps.lwsc.models.user_model import UserDB
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/categories", tags=["Categorys"])


def validate_bill_rates(category: Category):
    isValid = True
    message = ""

    index = 0

    lastTo = 0

    for rate in category.rate_list:
        if index == 0:
            # first item must start from zero
            if rate["From"] != 0:
                isValid = False
                message = "Billing bands must start from zero"
                break
        elif index == len(category.rate_list) - 1:
            # last item must end with zero
            if rate["To"] != 0:
                isValid = False
                message = "Billing bands must end with zero"
        else:
            # not first and not last. The start must match the last to
            if not rate["From"] == lastTo:
                isValid = False
                message = "Billing bands must start wit the previous end value"
                break

        # set last to
        lastTo = rate["To"]
        index += 1

    if not isValid:
        raise HTTPException(
            status_code=400,
            detail=f"The specified billing rate list is not : {message}",
        )


async def process_bill_rates(category: Category, db: AsyncSession):
    # remove existing rates
    await db.execute(delete(BillRateDB).where(BillRateDB.cat_id == category.id))
    await db.commit()

    for billrate in category.rate_list:

        db_rate = BillRateDB(
            # user
            user_id=category.user_id,
            # cat
            cat_id=category.id,
            # band
            name=billrate["Name"],
            order=billrate["Order"],
            from_vol=billrate["From"],
            to_vol=billrate["To"],
            rate=billrate["Rate"],
            # service
            created_by=category.created_by,
        )
        db.add(db_rate)

    await db.commit()


@router.post("/create", response_model=CategoryWithDetail)
async def post__category(category: Category, db: AsyncSession = Depends(get_lwsc_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == category.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id {category.user_id} does not exist",
        )

    validate_bill_rates(category)

    db_tran = CategoryDB(
        # user
        user_id=category.user_id,
        # transaction
        cat_name=category.cat_name,
        description=category.description,
        rate_list=category.rate_list,
        # service
        created_by=user.email,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)

        await process_bill_rates(db_tran, db)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create category: {e}")
    return db_tran


@router.put("/update/{cat_id}", response_model=CategoryWithDetail)
async def update_category(
    cat_id: int, category_update: Category, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(select(CategoryDB).where(CategoryDB.id == cat_id))
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=404, detail=f"Unable to find category with id '{cat_id}'"
        )

    validate_bill_rates(category_update)

    # Update fields that are not None
    for key, value in category_update.dict(exclude_unset=True).items():
        setattr(category, key, value)

    try:
        await db.commit()
        await db.refresh(category)

        await process_bill_rates(category, db)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update category {e}")
    return category


@router.get("/list", response_model=List[CategoryWithDetail])
async def list__categories(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(CategoryDB).options(
            selectinload(CategoryDB.user),
            selectinload(CategoryDB.stage),
            selectinload(CategoryDB.status),
        ).order_by(CategoryDB.cat_name))
    return result.scalars().all()

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    rate_domestic = [
        {"Name": "Band 1", "Order": 1, "From": 0.0, "To": 6.0, "Rate": 26.70},
        {
            "Name": "Band 2",
            "Order": 2,
            "From": 6.0,
            "To": 14.0,
            "Rate": 26.70,
        },
        {
            "Name": "Band 3",
            "Order": 3,
            "From": 14.0,
            "To": 30.0,
            "Rate": 26.70,
        },
        {"Name": "Band 4", "Order": 4, "From": 30.0, "To": 6.0, "Rate": 0},
    ]

    rate_commencial = [
        {
            "Name": "Band 1",
            "Order": 1,
            "From": 0.0,
            "To": 10.0,
            "Rate": 104.50,
        },
        {
            "Name": "Band 2",
            "Order": 2,
            "From": 10.0,
            "To": 0.0,
            "Rate": 2318.04,
        },
    ]

    typeList = [
        "Domestic",
        "Commercial",
        "GRZ",
    ]
    typeId = 1

    for value in typeList:
        db_category = CategoryDB(
            # personal details
            user_id=1,
            cat_name=value,
            rate_list=rate_domestic if value == "Domestic" else rate_commencial,
            # approval
            status_id=lwscapp.STATUS_APPROVED,
            stage_id=lwscapp.APPROVAL_STAGE_APPROVED,
            approval_levels=2,
        )
        db.add(db_category)
        typeId += 1

        try:
            await db.commit()
            await db.refresh(db_category)

            await process_bill_rates(db_category, db)

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400, detail=f"Unable to initialize category '{value}': f{e}"
            )
    return {
        "succeeded": True,
        "message": "Categories have been successfully initialized",
    }


@router.get("/id/{cat_id}", response_model=CategoryWithDetail)
async def get__category(cat_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(CategoryDB).where(CategoryDB.id == cat_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404, detail=f"Unable to find category with id '{cat_id}'"
        )
    return category
