from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.transaction_states_model import TransactionState, TransactionStateDB

router = APIRouter(prefix="/transaction-states", tags=["TransactionStates"])


@router.post("/create", response_model=TransactionState)
async def create_states(transaction: TransactionState, db: AsyncSession = Depends(get_db)):
    
    db_user = TransactionStateDB(
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
        raise HTTPException(status_code=400, detail=f"Unable to create transaction state: f{e}")
    return db_user

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_db)):
    transactionList = ['Open', 'Closed']
    transactionId = 1
    
    for value in transactionList:
        db_status = TransactionStateDB(
            #personal details
            id = transactionId,
            state_name=value,
        )
        db.add(db_status)
        transactionId += 1
        
    try:
        await db.commit()
        #await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to initialize transaction states: f{e}")
    return {'succeeded': True, 'message': 'Transaction states have been successfully initialized'}


@router.get("/", response_model=List[TransactionState])
async def list_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TransactionStateDB))
    return result.scalars().all()

