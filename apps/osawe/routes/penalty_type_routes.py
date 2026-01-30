from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.osawe.osawedb import get_osawe_db
from apps.osawe.models.penalty_types_model import PenaltyType, PenaltyTypeDB

router = APIRouter(prefix="/penalty-types", tags=["PenaltyTypes"])


@router.post("/create", response_model=PenaltyType)
async def create_type(transaction: PenaltyType, db: AsyncSession = Depends(get_osawe_db)):
    
    db_user = PenaltyTypeDB(
        #personal details
        id = transaction.id,
        type_name=transaction.type_name,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create penalty type: f{e}")
    return db_user

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_osawe_db)):
    penaltyList = ['Late Posting', 'Missed Meeting', 'Late Joining', 'Incorrect Posting']
    penaltyId = 1
    
    for value in penaltyList:
        db_status = PenaltyTypeDB(
            #personal details
            id = penaltyId,
            type_name=value,
        )
        db.add(db_status)
        penaltyId += 1
        
    try:
        await db.commit()
        #await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to initialize penalty types: f{e}")
    return {'succeeded': True, 'message': 'Penalty types have been successfully initialized'}


@router.get("/", response_model=List[PenaltyType])
async def list_types(db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(select(PenaltyTypeDB))
    return result.scalars().all()

