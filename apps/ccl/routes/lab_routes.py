from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy.orm import selectinload
from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.lab_model import Lab, LabDB, LabItem, LabWithDetail
from apps.ccl.models.user_model import UserDB

router = APIRouter(prefix="/labs", tags=["Labs"])


@router.post("/create", response_model=LabWithDetail)
async def create_item(lab: Lab, db: AsyncSession = Depends(get_ccl_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == lab.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{lab.user_id}' does not exist"
        )

    db_user = LabDB(
        # user
        user_id=lab.user_id,
        
        # details
        name=lab.name,
        description=lab.description,
        
        # service
        created_by=user.email,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create lab: f{e}")
    return db_user


@router.get("/id/{lab_id}", response_model=LabWithDetail)
async def get_item(lab_id: int, db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(LabDB)
        .options(
            selectinload(LabDB.user),
        )
        .filter(LabDB.id == lab_id)
        .order_by(LabDB.name)
    )

    lab = result.scalars().first()
    if not lab:
        raise HTTPException(
            status_code=404, detail=f"Unable to find lab with id '{lab_id}'"
        )
    return lab


@router.put("/update/{lab_id}", response_model=LabWithDetail)
async def update_item(
    lab_id: int, lab_update: Lab, db: AsyncSession = Depends(get_ccl_db)
):
    result = await db.execute(
        select(LabDB)
        .options(
            selectinload(LabDB.user),
        )
        .filter(LabDB.id == lab_id)
        .order_by(LabDB.name)
    )

    lab = result.scalar_one_or_none()

    if not lab:
        raise HTTPException(
            status_code=404, detail=f"Unable to find lab with id '{lab_id}'"
        )

    # Update fields that are not None
    for key, value in lab_update.dict(exclude_unset=True).items():
        setattr(lab, key, value)

    try:
        await db.commit()
        await db.refresh(lab)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update lab {e}")
    return lab


@router.get("/list", response_model=List[LabWithDetail])
async def list(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(LabDB)
        .options(
            selectinload(LabDB.user),
        )
        .order_by(LabDB.name)
    )
    return result.scalars().all()


@router.get("/items", response_model=List[LabItem])
async def list_items(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(LabDB)
        .options(
            selectinload(LabDB.user),
        )
        .order_by(LabDB.name)
    )
    return result.scalars().all()
