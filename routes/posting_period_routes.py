from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import calendar
from database import get_db
from models.posting_period_model import PostingPeriod, PostingPeriodDB

router = APIRouter(prefix="/posting-periods", tags=["PostingPeriods"])


@router.post("/create", response_model=PostingPeriod)
async def create_period(period: PostingPeriod, db: AsyncSession = Depends(get_db)):
    
    db_user = PostingPeriodDB(
        #personal details
        id = period.id,
        period_name = period.period_name,
        start_date = period.month,
        end_date = period.year,
        # approval
        status_id = period.status_id,
        stage_id = period.stage_id,
        approval_levels = period.approval_levels,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create posting period: f{e}")
    return db_user

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_db)):
    # Loop through years 2025 and 2026
    for yearNo in range(2025, 2027):
        # Loop through all months (1–12)
        for monthNo in range(1, 13):
           
            db_status = PostingPeriodDB(
            #personal details
            id = int(f'{yearNo}{monthNo}'),
            period_name = f'{calendar.month_name[monthNo]} {yearNo}',
            month = monthNo,
            year = yearNo,
            # approval
            status_id = 2,
            stage_id = 2,
            approval_levels = 2,
            )
            
            db.add(db_status)
            
    try:
        await db.commit()
        #await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to initialize posting periods: f{e}")
    return {'succeeded': True, 'message': 'Posting periods have been successfully initialized'}



@router.get("/list", response_model=List[PostingPeriod])
async def list_periods(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PostingPeriodDB))
    return result.scalars().all()

