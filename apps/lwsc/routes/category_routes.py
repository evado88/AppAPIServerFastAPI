from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.category_model import Category, CategoryDB, CategoryWithDetail
from apps.lwsc.models.user_model import UserDB

router = APIRouter(prefix="/categories", tags=["Categorys"])


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

    db_tran = CategoryDB(
        # user
        user_id=category.user_id,
        # transaction
        cat_name=category.cat_name,
        description=category.description,
        # service
        created_by=user.email,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create category: {e}")
    return db_tran


@router.put("/update/{cat_id}", response_model=CategoryWithDetail)
async def update_category(
    cat_id: int, category_update: Category, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(select(CategoryDB).where(CategoryDB.id == cat_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"Unable to find category with id '{cat_id}'"
        )

    # Update fields that are not None
    for key, value in category_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update category {e}")
    return config


@router.get("/list", response_model=List[CategoryWithDetail])
async def list__categories(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(CategoryDB))
    queries = result.scalars().all()
    return queries


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    typeList = [
        "Low Density",
        "Commercial",
        "GRZ",
        "OOP",
        "prisons",
        "Township",
        "Police Camp",
        "Medium",
        "Messengers",
        "Roads",
        "Suburbs",
        "Teachers",
        "ZESCO",
    ]
    typeId = 1

    for value in typeList:
        db_status = CategoryDB(
            # personal details
            user_id=1,
            cat_name=value,
        )
        db.add(db_status)
        typeId += 1

    try:
        await db.commit()
        # await db.refresh(db_status)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to initialize categories: f{e}"
        )
    return {
        "succeeded": True,
        "message": "Categories have been successfully initialized",
    }


@router.get("/id/{cat_id}", response_model=CategoryWithDetail)
async def get__category(cat_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(CategoryDB).filter(CategoryDB.id == cat_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404, detail=f"Unable to find category with id '{cat_id}'"
        )
    return category
