from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, joinedload
from typing import List

from database import get_db
from models.configuration_model import SACCOConfiguration, SACCOConfigurationDB, SACCOConfigurationWithDetail
from models.user_model import UserDB
from models.status_types_model import StatusTypeDB

router = APIRouter(prefix="/sacco-config", tags=["SACCOConfiguration"])


@router.post("/create", response_model=SACCOConfiguration)
async def post_config(config: SACCOConfiguration, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == config.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"User with id {config.user_id} does not exist"
        )

    db_tran = SACCOConfigurationDB(
        # user
        user_id = config.user_id,
        # posting
        late_posting_date_start = config.late_posting_date_start,
        
        saving_multiple = config.saving_multiple,
        shares_multiple = config.shares_multiple,
        social_min = config.social_min,
        
        loan_interest_rate = config.loan_interest_rate,
        loan_repayment_rate = config.loan_repayment_rate,
        loan_saving_ratio = config.loan_saving_ratio,
        
        late_posting_rate = config.late_posting_rate,
        missed_meeting_rate = config.missed_meeting_rate,
        late_meeting_rate = config.late_meeting_rate,
        
        approval_levels = config.approval_levels,
        #service columns
        updated_by = config.updated_by,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create configuration {e}")
    return db_tran

@router.put("/update/{config_id}", response_model=SACCOConfigurationWithDetail)
async def update_configuration(config_id: int, config_update: SACCOConfiguration, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SACCOConfigurationDB)
        .where(SACCOConfigurationDB.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Unable to find configuration with id '{config_id}' not found")
    
    # Update fields that are not None
    for key, value in config_update.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
        
    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update configuration {e}")
    return config

@router.get("/", response_model=List[SACCOConfigurationWithDetail])
async def list_configurations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SACCOConfigurationDB).options(
            joinedload(SACCOConfigurationDB.user),
        )
    )
    posting = result.scalars().all()
    return posting


@router.get("/{config_id}", response_model=SACCOConfigurationWithDetail)
async def get_configuration(config_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SACCOConfigurationDB)
        .options(
            joinedload(SACCOConfigurationDB.user),
        )
        .filter(SACCOConfigurationDB.id == config_id)
    )
    posting = result.scalars().first()
    if not posting:
        raise HTTPException(status_code=404, detail=f"Configuration with id '{config_id}' not found")
    return posting
