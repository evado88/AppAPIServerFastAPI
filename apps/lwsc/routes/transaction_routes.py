import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List

from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.customer_model import CustomerDB
from apps.lwsc.models.transaction_group_model import TransactionGroupDB
from apps.lwsc.models.transaction_model import (
    ParamTransactionEdit,
    Transaction,
    TransactionDB,
    TransactionWithDetail,
)
from apps.lwsc.models.transaction_type_model import TransactionTypeDB
from apps.lwsc.models.user_model import UserDB
from helpers import assist

import pandas as pd
import numpy as np
from datetime import date, datetime
from sqlalchemy import or_, desc
from sqlalchemy.orm import noload

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
        # attachement
        attachment_id=tran.attachment_id,
        # transaction
        date=tran.date,
        amount=tran.amount,
        comments=tran.comments,
        reference=tran.reference,
        # approval
        status_id=tran.status_id,
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
        .options(
            selectinload(TransactionDB.user),
            selectinload(TransactionDB.type),
            selectinload(TransactionDB.group),
            selectinload(TransactionDB.status),
            selectinload(TransactionDB.stage),
            selectinload(TransactionDB.attachment),
            selectinload(TransactionDB.customer),
        )
        .order_by(desc(TransactionDB.id))
    )
    transactions = result.scalars().all()
    return transactions


@router.get("/id/{tran_id}", response_model=ParamTransactionEdit)
async def get_transaction(tran_id: int, db: AsyncSession = Depends(get_lwsc_db)):

    # get transaction
    transactionItem = None
    if tran_id != 0:
        result = await db.execute(
            select(TransactionDB)
            .options(
                selectinload(TransactionDB.user),
                selectinload(TransactionDB.type),
                selectinload(TransactionDB.group),
                selectinload(TransactionDB.status),
                selectinload(TransactionDB.stage),
                selectinload(TransactionDB.attachment),
                selectinload(TransactionDB.customer),
            )
            .where(TransactionDB.id == tran_id)
        )
        transactionItem = result.scalars().first()
        if not transactionItem:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to find transaction with id '{tran_id}'",
            )

    # customer list
    result = await db.execute(select(CustomerDB).options(noload("*")))
    customerList = result.scalars().all()

    # get type list
    result = await db.execute(select(TransactionTypeDB).options(noload("*")))
    typeList = result.scalars().all()

    # get group list
    result = await db.execute(select(TransactionGroupDB).options(noload("*")))
    groupList = result.scalars().all()

    paramEdit = ParamTransactionEdit(
        transaction=transactionItem,
        customers=customerList,
        types=typeList,
        groups=groupList,
    )

    return paramEdit


@router.put("/update/{id}", response_model=ParamTransactionEdit)
async def update_transaction(
    id: int, transaction_update: Transaction, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(
        select(TransactionDB)
        .options(
            selectinload(TransactionDB.user),
            selectinload(TransactionDB.type),
            selectinload(TransactionDB.group),
            selectinload(TransactionDB.status),
            selectinload(TransactionDB.stage),
            selectinload(TransactionDB.attachment),
            selectinload(TransactionDB.customer),
        )
        .where(TransactionDB.id == id)
    )
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
    
    
    # customer list
    result = await db.execute(select(CustomerDB).options(noload("*")))
    customerList = result.scalars().all()

    # get type list
    result = await db.execute(select(TransactionTypeDB).options(noload("*")))
    typeList = result.scalars().all()

    # get group list
    result = await db.execute(select(TransactionGroupDB).options(noload("*")))
    groupList = result.scalars().all()

    paramEdit = ParamTransactionEdit(
        transaction=transaction,
        customers=customerList,
        types=typeList,
        groups=groupList,
    )

    return paramEdit
