from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.attendance_types_model import AttendanceType, AttendanceTypeDB

router = APIRouter(prefix="/attendance-types", tags=["AttendanceTypes"])


@router.post("/create", response_model=AttendanceType)
async def create_type(status: AttendanceType, db: AsyncSession = Depends(get_db)):
    
    db_user = AttendanceTypeDB(
        #personal details
        id = status.id,
        type_name = status.type_name,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create attendance type: f{e}")
    return db_user

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_db)):
    typeList = ['In-Person', 'Virtual', 'Late', 'Absent']
    typeId = 1
    
    for value in typeList:
        db_status = AttendanceTypeDB(
            #personal details
            id = typeId,
            type_name = value,
        )
        db.add(db_status)
        typeId += 1
        
    try:
        await db.commit()
        #await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unbale to initialize attendance types: f{e}")
    return {'succeeded': True, 'message': 'Attendance types has been successfully initialized'}


@router.get("/", response_model=List[AttendanceType])
async def list_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AttendanceTypeDB))
    return result.scalars().all()

