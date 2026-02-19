from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.lab_model import Lab, LabDB, LabWithDetail
from apps.ccl.models.user_model import UserDB

router = APIRouter(prefix="/labs", tags=["Labs"])


@router.post("/create", response_model=LabWithDetail)
async def create(lab: Lab, db: AsyncSession = Depends(get_ccl_db)):
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
        raise HTTPException(
            status_code=400, detail=f"Unable to create lab: f{e}"
        )
    return db_user

@router.get("/id/{lab_id}", response_model=LabWithDetail)
async def get_item(lab_id: int, db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(LabDB)
        .filter(LabDB.id == lab_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Unable to find lab with id '{lab_id}'")
    return category


@router.put("/update/{lab_id}", response_model=LabWithDetail)
async def update_item(lab_id: int, lab_update: Lab, db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(LabDB)
        .where(LabDB.id == lab_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Unable to find lab with id '{lab_id}'")
    
    # Update fields that are not None
    for key, value in lab_update.dict(exclude_unset=True).items():
        setattr(config, key, value)
        
    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update lab {e}")
    return config

@router.get("/list", response_model=List[LabWithDetail])
async def list_items(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(LabDB))
    return result.scalars().all()
