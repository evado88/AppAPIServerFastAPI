from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.osawe.osawedb import get_osawe_db
from apps.osawe.models.transaction_group_model import TransactionGroup, TransactionGroupDB
from apps.osawe.models.user_model import UserDB

router = APIRouter(prefix="/transaction-groups", tags=["TransactionGroups"])


@router.post("/create", response_model=TransactionGroup)
async def create_type(group: TransactionGroup, db: AsyncSession = Depends(get_osawe_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == group.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{group.user_id}' does not exist"
        )
        
    db_user = TransactionGroupDB(
        # user
        user_id=group.user_id,
        # details
        group_name=group.group_name,
        description=group.description,
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
            status_code=400, detail=f"Unable to create transaction group: f{e}"
        )
    return db_user

@router.get("/id/{group_id}", response_model=TransactionGroup)
async def get_knowledgebase_category(group_id: int, db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(
        select(TransactionGroupDB)
        .filter(TransactionGroupDB.id == group_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Unable to find group with id '{group_id}'")
    return category


@router.put("/update/{group_id}", response_model=TransactionGroup)
async def update_category(group_id: int, group_update: TransactionGroup, db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(
        select(TransactionGroupDB)
        .where(TransactionGroupDB.id == group_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Unable to find group with id '{group_id}'")
    
    # Update fields that are not None
    for key, value in group_update.dict(exclude_unset=True).items():
        setattr(config, key, value)
        
    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update group {e}")
    return config

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_osawe_db)):
    typeList = [
        "Cash at Bank Interest",
        "Logistics",
        "Surveyor",
        "Legal",
        "Land Survey",
        "Chief",
        "Google Meets Expense",
        "Land",
        "OSAWE Payout Works",
    ]
    groupId = 1

    for value in typeList:
        db_status = TransactionGroupDB(
            # personal details
            user_id=1,
            group_name=value,
        )
        db.add(db_status)
        groupId += 1

    try:
        await db.commit()
        # await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to initialize transaction groups: f{e}"
        )
    return {
        "succeeded": True,
        "message": "Transaction groups have been successfully initialized",
    }


@router.get("/list", response_model=List[TransactionGroup])
async def list_groups(db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(select(TransactionGroupDB))
    return result.scalars().all()
