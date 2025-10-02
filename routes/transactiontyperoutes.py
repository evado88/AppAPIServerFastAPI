from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.transaction_types_model import TransactionType, TransactionTypeDB

router = APIRouter(prefix="/transaction-types", tags=["TransactionTypes"])


@router.post("/create", response_model=TransactionType)
async def create_status(transaction: TransactionType, db: AsyncSession = Depends(get_db)):
    
    db_user = TransactionTypeDB(
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
        raise HTTPException(status_code=400, detail=f"Could not register create transaction type: f{e}")
    return db_user

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_db)):
    transactionList = ['Saving', 'Share', 'Loan', 'Penalty', 'Interest', 'Social Fund']
    transactionId = 1
    
    for value in transactionList:
        db_status = TransactionTypeDB(
            #personal details
            id = transactionId,
            type_name=value,
        )
        db.add(db_status)
        transactionId += 1
        
    try:
        await db.commit()
        #await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not initialize transaction types: f{e}")
    return {'succeeded': True, 'message': 'Transaction type list has been successfully initialzied'}


@router.get("/", response_model=List[TransactionType])
async def list_statuses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TransactionTypeDB))
    return result.scalars().all()

