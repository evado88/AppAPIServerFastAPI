from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, joinedload
from typing import List

from database import get_db
from helpers import assist
from models.param_models import (
    ParamMemberSummary,
    ParamGroupSummary,
    ParamMemberTransaction,
    ParamSummary,
)
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


@router.get("/member-summary/{userId}", response_model=List[ParamSummary])
async def get_member_summary(userId: int, db: AsyncSession = Depends(get_db)):
    # get user
    result = await db.execute(select(UserDB).where(UserDB.id == userId))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id {userId} does not exist"
        )

    # get all transaction types
    result = await db.execute(select(TransactionTypeDB))
    types = result.scalars().all()

    summary = [{"id": type.id, "name": type.type_name, "amount": 0} for type in types]

    # get available transactions
    stmt = (
        select(
            TransactionTypeDB.type_name,
            func.coalesce(func.sum(TransactionDB.amount), 0).label("amount"),
        )
        .outerjoin(TransactionDB, TransactionTypeDB.id == TransactionDB.type_id)
        .filter(TransactionDB.user_id == userId)
        .group_by(TransactionTypeDB.type_name)
    )

    result = await db.execute(stmt)
    rows = result.all()
    # map transactions to base items
    for item in summary:
        for row in rows:
            if row[0] == item["name"]:
                item["amount"] = row[1]
                break

    return summary


@router.get("/summary/all", response_model=List[ParamSummary])
async def get_all_member_summary(db: AsyncSession = Depends(get_db)):
    # get all transaction types
    result = await db.execute(select(TransactionTypeDB))
    types = result.scalars().all()

    summary = [{"id": type.id, "name": type.type_name, "amount": 0} for type in types]

    # get available transactions
    stmt = (
        select(
            TransactionTypeDB.type_name,
            func.coalesce(func.sum(TransactionDB.amount), 0).label("amount"),
        )
        .outerjoin(TransactionDB, TransactionTypeDB.id == TransactionDB.type_id)
        .group_by(TransactionTypeDB.type_name)
    )

    result = await db.execute(stmt)
    rows = result.all()
    # map transactions to base items
    for item in summary:
        for row in rows:
            if row[0] == item["name"]:
                item["amount"] = row[1]
                break

    return summary


@router.get("/year-to-date/all", response_model=List[ParamMemberSummary])
async def get_all_member_ytd(db: AsyncSession = Depends(get_db)):
    print("starting summary", assist.get_current_date(False))
    # get all users
    result = await db.execute(select(UserDB).filter(UserDB.role == assist.USER_MEMBER))
    users = result.scalars().all()

    # get all transaction types
    result = await db.execute(select(TransactionTypeDB))
    types = result.scalars().all()

    # create a summary
    summary = [
        {
            "id": user.id,
            "fname": user.fname,
            "lname": user.lname,
            "email": user.email,
            "phone": user.mobile,
        }
        for user in users
    ]

    # add transaction info
    for member in summary:
        for type in types:
            member[f"tid{type.id}"] = 0.0

    # get available transactions
    stmt = (
        select(
            TransactionDB.user_id,
            TransactionDB.type_id,
            func.coalesce(func.sum(TransactionDB.amount), 0).label("amount"),
        )
        .filter(
            TransactionDB.status_id == assist.STATUS_APPROVED,
        )
        .group_by(TransactionDB.user_id, TransactionDB.type_id)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # map transactions to base items
    for member in summary:
        for tran in rows:
            if member["id"] == tran["user_id"]:
                tid = tran["type_id"]
                member[f"tid{tid}"] = tran["amount"]

    print("ending summary", assist.get_current_date(False))

    return summary


@router.get("/transaction-summary/all", response_model=List[ParamMemberTransaction])
async def get_all_member_transaction_summary(db: AsyncSession = Depends(get_db)):

    # create a summary
    summary = []

    # get available transactions
    result = await db.execute(
        select(TransactionDB).filter(
            TransactionDB.status_id == assist.STATUS_APPROVED,
        )
    )
    rows = result.scalars().all()

    # map transactions to base items
    for tran in rows:
        summary.append(
            {
                "id": tran.id,
                "name": f'{tran.user.fname} {tran.user.lname}',
                "email": tran.user.email,
                "phone": tran.user.mobile,
                "type": tran.date.strftime("%B %Y"),
                "period": tran.type.type_name,
                "amount": tran.amount,
            }
        )

    return summary
