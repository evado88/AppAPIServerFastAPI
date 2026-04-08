from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List


from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.transaction_type_model import TransactionType, TransactionTypeDB

router = APIRouter(prefix="/transaction-types", tags=["TransactionTypes"])


@router.post("/create", response_model=TransactionType)
async def create_type(transaction: TransactionType, db: AsyncSession = Depends(get_lwsc_db)):

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
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    transactionList = [
        "Payment", # customer paid
        "Bill", # customer is owing
        "Adjustment (Credit)", # customer paid
        "Adjustment (Debit)", # customer is owing
        "Reversal (Credit)", # cancel incorrect payment, customer paid
        "Reversal (Debit)", # cancel incorrect payment, customer is owing
    ]
    transactionId = 1

    for value in transactionList:
        db_status = TransactionTypeDB(
            # personal details
            id=transactionId,
            type_name=value,
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


@router.get("/list", response_model=List[TransactionType])
async def list_types(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(TransactionTypeDB).order_by(TransactionTypeDB.id))
    return result.scalars().all()
