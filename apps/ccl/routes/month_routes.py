from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.month_model import Month, MonthDB

router = APIRouter(prefix="/months", tags=["Months"])


@router.post("/create", response_model=Month)
async def create_status(status: Month, db: AsyncSession = Depends(get_ccl_db)):
    
    db_user = MonthDB(
        #personal details
        id = status.id,
        month_name=status.month_name,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create month: f{e}")
    return db_user

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_ccl_db)):
    months = [
    { 'number': 1, 'name': "January" },
    { 'number': 2, 'name': "February" },
    { 'number': 3, 'name': "March" },
    { 'number': 4, 'name': "April" },
    { 'number': 5, 'name': "May" },
    { 'number': 6, 'name': "June" },
    { 'number': 7, 'name': "July" },
    { 'number': 8, 'name': "August" },
    { 'number': 9, 'name': "September" },
    { 'number': 10, 'name': "October" },
    { 'number': 11, 'name': "November" },
    { 'number': 12, 'name': "December" }]
   
    statusId = 1
    
    for value in months:
        db_status = MonthDB(
            #personal details
            id = value["number"],
            month_name=value["name"],
        )
        db.add(db_status)
        statusId += 1
        
    try:
        await db.commit()
        #await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to initialize months: f{e}")
    return {'succeeded': True, 'message': 'Months have been successfully initialized'}


@router.get("/list", response_model=List[Month])
async def list_statuses(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(MonthDB))
    return result.scalars().all()

