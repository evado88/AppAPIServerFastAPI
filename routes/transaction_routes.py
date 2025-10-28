from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, joinedload
from typing import List

from database import get_db
from models.transaction_model import Transaction, TransactionDB, TransactionWithDetail
from models.user_model import UserDB
from models.transaction_types_model import TransactionTypeDB
from models.transaction_sources_model import TransactionSourceDB
from models.status_types_model import StatusTypeDB

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=Transaction)
async def post_transaction(tran: Transaction, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == tran.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id {tran.user_id} does not exist"
        )

    db_tran = TransactionDB(
        # id
        type_id=tran.type_id,
        penalty_type_id=tran.penalty_type_id,
        # user
        user_id=tran.user_id,
        # transaction
        date=tran.date,
        source_id=tran.source_id,
        amount=tran.amount,
        comments=tran.comments,
        reference=tran.reference,
        # loan
        term_months=tran.term_months,
        interest_rate=tran.interest_rate,
        # loan payment transaction id
        parent_id=tran.parent_id,
        # approval
        status_id=tran.status_id,
        state_id=tran.state_id,
        stage_id=tran.stage_id,
        approval_levels=tran.approval_levels,
        # service
        created_by=tran.created_by,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to create transaction: {e}"
        )
    return db_tran


@router.get("/", response_model=List[TransactionWithDetail])
async def list_transactions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TransactionDB)
        # .options(
        #    joinedload(TransactionDB.post),
        #    joinedload(TransactionDB.status),
        #    joinedload(TransactionDB.type),
        #    joinedload(TransactionDB.source),
        #
        # )
    )
    transactions = result.scalars().all()
    return transactions


@router.get(
    "/user/{userId}/type/{typeId}/status/{statusId}",
    response_model=List[TransactionWithDetail],
)
async def list_user_status_transactions(
    userId: int, typeId: int, statusId: int, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TransactionDB)
        # .options(
        #    joinedload(TransactionDB.post),
        #    joinedload(TransactionDB.status),
        #    joinedload(TransactionDB.type),
        #    joinedload(TransactionDB.source),
        #
        # )
        .filter(
            TransactionDB.status_id == statusId,
            TransactionDB.user_id == userId,
            TransactionDB.type_id == typeId,
        )
    )
    transactions = result.scalars().all()
    return transactions


@router.get("/{tran_id}", response_model=TransactionWithDetail)
async def get_transaction(tran_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TransactionDB)
        # .options(
        #    joinedload(TransactionDB.post),
        #    joinedload(TransactionDB.status),
        #    joinedload(TransactionDB.type),
        #    joinedload(TransactionDB.source),
        #
        # )
        .filter(TransactionDB.id == tran_id)
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(
            status_code=404, detail=f"Unable to find transaction with id '{tran_id}'"
        )
    return transaction
