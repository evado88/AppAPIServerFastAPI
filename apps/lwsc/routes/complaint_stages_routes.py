from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.complaint_stages_model import ComplaintStage, ComplaintStageDB

router = APIRouter(prefix="/complaint-stages", tags=["ComplaintStages"])


@router.post("/create", response_model=ComplaintStage)
async def create_stage(status: ComplaintStage, db: AsyncSession = Depends(get_lwsc_db)):

    db_user = ComplaintStageDB(
        # personal details
        id=status.id,
        stage_name=status.stage_name,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to create complaint stage: f{e}"
        )
    return db_user


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    stageList = [
        "Open", #1 just submitted
        "In Progress",#2 being worked on
        "Resolved",#3 item resolved
        "Closed",#4 item closed
    ]
    stageId = 1

    for value in stageList:
        db_status = ComplaintStageDB(
            # personal details
            id=stageId,
            stage_name=value,
        )
        db.add(db_status)
        stageId += 1

    try:
        await db.commit()
        # await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to initialize complaint stages: f{e}"
        )
    return {
        "succeeded": True,
        "message": f"{len(stageList)} Complaint stages have been successfully initialized",
    }


@router.get("/list", response_model=List[ComplaintStage])
async def list_stages(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(ComplaintStageDB))
    return result.scalars().all()
