from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, joinedload
from typing import List

from database import get_db
from models.transactionmodel import Transaction, TransactionDB, TransactionWithDetail
from models.usermodel import UserDB
from models.transaction_types_model import TransactionTypeDB
from models.status_types_model import StatusTypeDB

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=Transaction)
async def create_loan(tran: Transaction, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == tran.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail=f"User with id {tran.user_id} does not exist")

    db_tran = TransactionDB(
        #id
        type_id = tran.type_id,
        #user
        user_id = tran.user_id,
        #transaction
        amount = tran.amount,
        comments = tran.comments,
        reference = tran.reference,
        #loan
        term_months = tran.term_months,
        interest_rate = tran.interest_rate,
        #approval
        status_id = tran.status_id,
        approval_levels =tran.approval_levels,
        #service
        created_by = tran.created_by
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Could not create loan")
    return db_tran


@router.get("/", response_model=List[TransactionWithDetail])
async def list_transactions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TransactionDB))
    transactions = result.scalars().all()
    return transactions


@router.get("/{tran_id}", response_model=TransactionWithDetail)
async def get_transaction(tran_id: int, db: AsyncSession = Depends(get_db)):
    transactions = (
        db.query(TransactionDB)
        .options(
            joinedload(StatusTypeDB),
            joinedload(TransactionTypeDB),
        )
        .all()
    )
    return transactions