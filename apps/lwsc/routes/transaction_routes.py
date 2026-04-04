import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, joinedload
from typing import List

from apps.lwsc.models.transaction_model import (
    Transaction,
    TransactionDB,
    TransactionWithDetail,
)
from apps.lwsc.models.user_model import UserDB
from apps.osawe.osawedb import get_lwsc_db
from helpers import assist

import pandas as pd
import numpy as np
from datetime import date, datetime
from sqlalchemy import or_

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/create", response_model=Transaction)
async def post_transaction(tran: Transaction, db: AsyncSession = Depends(get_lwsc_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == tran.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id {tran.user_id} does not exist"
        )

    db_tran = TransactionDB(
        # type of transaction
        type_id=tran.type_id,
        # group of transaction
        group_id=tran.group_id,
        # user
        user_id=tran.user_id,
        # customer
        customer_id=tran.customer_id,
        # meter
        meter_id=tran.meter_id,
        # attachement
        attachment_id=tran.attachment_id,
        # transaction
        date=tran.date,
        amount=tran.amount,
        comments=tran.comments,
        reference=tran.reference,
        # approval
        status_id=tran.status_id,
        state_id=tran.state_id,
        stage_id=tran.stage_id,
        approval_levels=tran.approval_levels,
        # service
        created_by=user.email,
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


@router.get("/list", response_model=List[TransactionWithDetail])
async def list_transactions(db: AsyncSession = Depends(get_lwsc_db)):
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
    userId: int, typeId: int, statusId: int, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(
        select(TransactionDB).filter(
            TransactionDB.status_id == statusId,
            TransactionDB.user_id == userId,
            TransactionDB.type_id == typeId,
        )
    )
    transactions = result.scalars().all()
    return transactions


@router.get("/id/{tran_id}", response_model=TransactionWithDetail)
async def get_transaction(tran_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(TransactionDB).filter(TransactionDB.id == tran_id))
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(
            status_code=404, detail=f"Unable to find transaction with id '{tran_id}'"
        )
    return transaction


@router.put("/update/{id}", response_model=TransactionWithDetail)
async def update_transaction(
    id: int, transaction_update: Transaction, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(select(TransactionDB).where(TransactionDB.id == id))
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find transaction with id '{id}'",
        )

    # Update fields that are not None
    for key, value in transaction_update.dict(exclude_unset=True).items():
        setattr(transaction, key, value)

    try:
        await db.commit()
        await db.refresh(transaction)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update transaction {e}")
    return transaction
