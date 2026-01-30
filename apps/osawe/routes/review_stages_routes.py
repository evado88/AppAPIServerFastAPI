from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.osawe.osawedb import get_osawe_db
from apps.osawe.models.review_stages_model import ReviewStage, ReviewStageDB

router = APIRouter(prefix="/review-stages", tags=["ReviewStages"])


@router.post("/create", response_model=ReviewStage)
async def create_stage(status: ReviewStage, db: AsyncSession = Depends(get_osawe_db)):

    db_user = ReviewStageDB(
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
            status_code=400, detail=f"Unable to create review stage: f{e}"
        )
    return db_user


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_osawe_db)):
    stageList = [
        "Awaiting Submission", #1 before submission (all)
        "Submitted",#2 after submission
        "Primary Approval",#3 first admin reviews
        #monthly postings
        "Secondary Approval",#4 second admin reviews
        "Guarantor Approval",#5 member guarantor reviews (postings only)
        "Awaiting POP Upload",#6 waiting for pop upload (postings only)
        "Awaiting POP Approval",#7 waitng for pop approval (postings only)
        "Approved",#8 approved, third admin reviews
        ##posting periods
        "Guarantor Approvals",#9 member guarantor reviews (postings only)
        "Awaiting POP Uploads",#10 waiting for pop upload (postings only)
        "Awaiting POP Approvals",#10 waiting for pop upload (postings only)
        "Posted", #11
    ]
    stageId = 1

    for value in stageList:
        db_status = ReviewStageDB(
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
            status_code=400, detail=f"Unable to initialize review stages: f{e}"
        )
    return {
        "succeeded": True,
        "message": "Review stages have been successfully initialized",
    }


@router.get("/", response_model=List[ReviewStage])
async def list_stages(db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(select(ReviewStageDB))
    return result.scalars().all()
