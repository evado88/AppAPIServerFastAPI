from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.transaction_types_model import TransactionType, TransactionTypeDB

router = APIRouter(prefix="/transaction-types", tags=["TransactionTypes"])


@router.post("/create", response_model=TransactionType)
async def create_type(transaction: TransactionType, db: AsyncSession = Depends(get_db)):

    db_user = TransactionTypeDB(
        # personal details
        id=transaction.id,
        type_name=transaction.type_name,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to create transaction type: f{e}"
        )
    return db_user


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_db)):
    transactionList = [
        {"name": "Saving", "type": 1},#1
        {"name": "Share", "type": 1},#2
        {"name": "Loan", "type": 2},#3
        {"name": "Loan Payment", "type": 2},#4
        {"name": "Interest Charged", "type": 3},#5
        {"name": "Interest Earned", "type": 1},#6
        {"name": "Social Fund", "type": 1},#7
        {"name": "Penalty Charged", "type": 3},#8
        {"name": "Penalty Earned", "type": 1},#9
    ]
    transactionId = 1

    for value in transactionList:
        db_status = TransactionTypeDB(
            # personal details
            id=transactionId,
            type_category=value['type'],
            type_name=value['name'],
        )
        db.add(db_status)
        transactionId += 1

    try:
        await db.commit()
        # await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to initialize transaction types: f{e}"
        )
    return {
        "succeeded": True,
        "message": "Transaction types have been successfully initialized",
    }


@router.get("/", response_model=List[TransactionType])
async def list_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TransactionTypeDB))
    return result.scalars().all()
