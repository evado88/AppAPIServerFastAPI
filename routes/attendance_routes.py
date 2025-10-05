from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.attendance_model import Attendance, AttendanceDB, AttendanceWithDetail
from models.user_model import UserDB

router = APIRouter(prefix="/attendances", tags=["Attendances"])


@router.post("/", response_model=Attendance)
async def post_attendance(attendance: Attendance, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == attendance.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{attendance.user_id}' does not exist"
        )

    db_tran = AttendanceDB(
        # user
        user_id = attendance.user_id,
        type_id = attendance.type_id,
        meeting_id = attendance.meeting_id,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create attendance: {e}")
    return db_tran


@router.get("/", response_model=List[AttendanceWithDetail])
async def list_attendances(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AttendanceDB)
        #.options(
        #    joinedload(AttendanceDB.post),
        #    joinedload(AttendanceDB.status),
        #    joinedload(AttendanceDB.type),
        #    joinedload(AttendanceDB.source),
        #
        #)
    )
    attendances = result.scalars().all()
    return attendances


@router.get("/{attendance_id}", response_model=AttendanceWithDetail)
async def get_attendance(attendance_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AttendanceDB)
        #.options(
        #    joinedload(AttendanceDB.post),
        #    joinedload(AttendanceDB.status),
        #    joinedload(AttendanceDB.type),
        #    joinedload(AttendanceDB.source),
        #
        #)
        .filter(AttendanceDB.id == attendance_id)
    )
    attendance = result.scalars().first()
    if not attendance:
        raise HTTPException(status_code=404, detail=f"Unable to find attendance with id '{attendance_id}'")
    return attendance
