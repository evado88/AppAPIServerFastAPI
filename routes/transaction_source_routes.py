from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.transaction_sources_model import TransactionSource, TransactionSourceDB

router = APIRouter(prefix="/transaction-sources", tags=["TransactionSources"])


@router.post("/create", response_model=TransactionSource)
async def create_status(transaction: TransactionSource, db: AsyncSession = Depends(get_db)):
    
    db_user = TransactionSourceDB(
        #personal details
        id = transaction.id,
        source_name=transaction.source_name,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not register create transaction source: f{e}")
    return db_user

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_db)):
    transactionList = ['Bank Transfer', 'Mobile Money - Airtel', 'Mobile Money - MTN', 'Mobile Money - Zamtel', 'Cash', 'Cheque']
    transactionId = 1
    
    for value in transactionList:
        db_status = TransactionSourceDB(
            #personal details
            id = transactionId,
            source_name=value,
        )
        db.add(db_status)
        transactionId += 1
        
    try:
        await db.commit()
        #await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not initialize transaction sources: f{e}")
    return {'succeeded': True, 'message': 'Transaction source list has been successfully initialzied'}


@router.get("/", response_model=List[TransactionSource])
async def list_statuses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TransactionSourceDB))
    return result.scalars().all()

