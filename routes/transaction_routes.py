import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, joinedload
from typing import List

from database import get_db
from helpers import assist
from models.member_model import MemberDB
from models.param_models import (
    ParamInterestSharingSummary,
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
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import or_

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


@router.get("/interest-sharing/all", response_model=ParamInterestSharingSummary)
async def get_all_member_interest_sharing(db: AsyncSession = Depends(get_db)):
    print("starting all member interest sharing", assist.get_current_date(False))
    # get all users
    result = await db.execute(select(MemberDB))
    users = result.scalars().all()

    # create a summary for all members
    summary = [
        {
            "id": user.id,
            "fname": user.fname,
            "lname": user.lname,
            "email": user.email,
            "phone": user.mobile1,
            "bank_name": user.bank_name,
            "branch_name": user.bank_branch_name,
            "branch_code": user.bank_branch_code,
            "bank_account_no": user.bank_account_no,
            "bank_account_name": user.bank_account_name,
            "itotal": 0,
            "stotal": 0,
            "loan_total": 0,
            "loan_interest_total": 0,
            "loan_repayment_total": 0,
            "loan_plus_interest_total": 0,
            "loan_balance": 0,
            "time_value_total": 0,
            "proportional_final_share": 0,
            "payout_balance": 0,
            "tsavings": {"id": "Member Savings"},
            "isharing": {"id": "Member Sharing"},
        }
        for user in users
    ]

    # add transaction info
    for member in summary:
        for m in range(1, 13):
            member["tsavings"][f"m{m}"] = 0

    # get total savings for member per month
    stmt = (
        select(
            TransactionDB.user_id,
            TransactionDB.type_id,
            func.extract("year", TransactionDB.date).label("year"),
            func.extract("month", TransactionDB.date).label("month"),
            func.coalesce(func.sum(TransactionDB.amount), 0).label("amount"),
        )
        .filter(
            TransactionDB.status_id == assist.STATUS_APPROVED,
        )
        .group_by(
            TransactionDB.user_id,
            TransactionDB.type_id,
            func.extract("year", TransactionDB.date).label("year"),
            func.extract("month", TransactionDB.date).label("month"),
        )
    )

    result = await db.execute(stmt)
    memberRows = result.all()

    # get group total savings, interest and loans per month
    stmt = (
        select(
            TransactionDB.type_id,
            func.extract("year", TransactionDB.date).label("year"),
            func.extract("month", TransactionDB.date).label("month"),
            func.coalesce(func.sum(TransactionDB.amount), 0).label("amount"),
        )
        .filter(
            TransactionDB.status_id == assist.STATUS_APPROVED,
            or_(
                TransactionDB.type_id == assist.TRANSACTION_SAVINGS,
                TransactionDB.type_id == assist.TRANSACTION_LOAN,
                TransactionDB.type_id == assist.TRANSACTION_INTEREST_CHARGED,
            ),
        )
        .group_by(
            TransactionDB.type_id,
            func.extract("year", TransactionDB.date).label("year"),
            func.extract("month", TransactionDB.date).label("month"),
        )
    )

    result = await db.execute(stmt)
    totalRows = result.all()

    # get all totals
    totals = {
        "total_loan_balance": 0,
        "group_time_value_total": 0,
        "group_proportional_final_share": 0,
        "group_share_total": 0,
        "group_money_growth_total": 0,
        "group_money_growth_percent": 0,
        "group_payout_balance": 0,
        f"t{assist.TRANSACTION_SAVINGS}": {"id": "Group Savings"},
        f"t{assist.TRANSACTION_LOAN}": {"id": "Group Loans"},
        f"t{assist.TRANSACTION_INTEREST_CHARGED}": {"id": "Group Interest"},
        f"r1": {"id": "Current Month Loan/Savings Proportion"},
        f"r2": {"id": "Cummulative Month Loan/Savings Proportion"},
        f"r3": {"id": "Interest rate"},
    }

    for m in range(1, 13):
        totals[f"t{assist.TRANSACTION_SAVINGS}"][f"m{m}"] = 0
        totals[f"t{assist.TRANSACTION_LOAN}"][f"m{m}"] = 0
        totals[f"t{assist.TRANSACTION_INTEREST_CHARGED}"][f"m{m}"] = 0
        totals[f"r1"][f"m{m}"] = 0
        totals[f"r2"][f"m{m}"] = 0

    # map total transactions to base items
    for tran in totalRows:
        tid = tran["type_id"]
        mid = tran["month"]
        totals[f"t{tid}"][f"m{mid}"] = tran["amount"]

    # calculate row 1 and row 2
    for m in range(1, 13):
        # get savings, loans and interest
        savings = totals[f"t{assist.TRANSACTION_SAVINGS}"][f"m{m}"]
        loans = totals[f"t{assist.TRANSACTION_LOAN}"][f"m{m}"]

        # get interest rate
        if m < 10:
            rate = 0.10
        elif m == 10:
            rate = 0.075
        elif m == 11:
            rate = 0.05
        else:
            rate = 0.025

        # set rows
        totals[f"r1"][f"m{m}"] = (
            round(loans * rate, 3) if savings >= loans else round(savings * rate, 3)
        )
        totals[f"r2"][f"m{m}"] = (
            0 if savings >= loans else round(((loans - savings) * rate), 3)
        )

    # calculate interest rates
    for m in range(1, 13):
        # get interest rate

        if m < 10:
            rate = 0.10
        elif m == 10:
            rate = 0.075
        elif m == 11:
            rate = 0.05
        else:
            rate = 0.025
        # set rows
        totals[f"r3"][f"m{m}"] = rate

    # map transactions to base items
    for member in summary:
        # set transactions
        for tran in memberRows:
            if member["id"] == tran["user_id"]:
                if tran["type_id"] == assist.TRANSACTION_SAVINGS:
                    mid = tran["month"]

                    # set saving
                    member["tsavings"][f"m{mid}"] = tran["amount"]

                elif tran["type_id"] == assist.TRANSACTION_LOAN:
                    # set loan total
                    member["loan_total"] += tran["amount"]
                elif tran["type_id"] == assist.TRANSACTION_INTEREST_CHARGED:
                    # set loan interest total
                    member["loan_interest_total"] += tran["amount"]
                elif tran["type_id"] == assist.TRANSACTION_LOAN_PAYMENT:
                    # set loan payment total
                    member["loan_repayment_total"] += tran["amount"]

        # set sharing
        for m in range(1, 13):

            sharing = 0
            msavings = member["tsavings"][f"m{m}"]
            r1 = totals[f"r1"][f"m{m}"]
            r2 = totals[f"r2"][f"m{m}"]
            tsavinsg = totals[f"t{assist.TRANSACTION_SAVINGS}"][f"m{m}"]
            tinterest = totals[f"t{assist.TRANSACTION_INTEREST_CHARGED}"][f"m{m}"]

            if m == 1:
                if tsavinsg == 0:
                    # will produce error, set zero
                    sharing = 0
                else:
                    # calculate
                    sharing = round((msavings / tsavinsg) * tinterest, 3)
            else:
                # get total upto current month
                memberSavingTotal = 0
                groupSavingTotal = 0

                for mindex in range(1, m):
                    memberSavingTotal += member["tsavings"][f"m{mindex}"]
                    groupSavingTotal += totals[f"t{assist.TRANSACTION_SAVINGS}"][
                        f"m{mindex}"
                    ]

                if tsavinsg == 0 or groupSavingTotal == 0:
                    # will produce error, set zero
                    sharing = 0
                else:
                    # calcute
                    sharing1 = round((msavings / tsavinsg) * r1, 3)
                    sharing2 = round((memberSavingTotal / groupSavingTotal) * r2, 3)

                    sharing = sharing1 + sharing2

            member["isharing"][f"m{m}"] = sharing

        # set sharing totals
        totalMemberSharing = 0
        totalMemberSavings = 0

        for mindex in range(1, 13):
            totalMemberSharing += member["isharing"][f"m{mindex}"]
            totalMemberSavings += member["tsavings"][f"m{mindex}"]

        member["itotal"] = totalMemberSharing
        member["stotal"] = totalMemberSavings

        # set calculated fields
        member["loan_plus_interest_total"] = (
            member["loan_total"] + member["loan_interest_total"]
        )
        member["loan_balance"] = (
            member["loan_plus_interest_total"] - member["loan_repayment_total"]
        )
        member["time_value_total"] = member["stotal"] + member["itotal"]

        totals["total_loan_balance"] += member["loan_balance"]

        totals["group_time_value_total"] += member["time_value_total"]

        totals["group_share_total"] += member["stotal"]

    # calculate proportional share for each member
    for member in summary:

        member["proportional_final_share"] = round(
            (member["time_value_total"] / totals["group_time_value_total"])
            * totals["total_loan_balance"],
            3,
        )

        member["payout_balance"] = (
            member["proportional_final_share"] - member["loan_balance"]
        )

        totals["group_proportional_final_share"] += member["proportional_final_share"]
        totals["group_payout_balance"] += member["payout_balance"]

    totals["group_money_growth_total"] = (
        totals["group_proportional_final_share"] - totals["group_share_total"]
    )

    totals["group_money_growth_percent"] = round(
        (totals["group_money_growth_total"] / totals["group_share_total"]) * 100, 0
    )

    totals["group_payout_balance"] = round(totals["group_payout_balance"], 1)

    fullSummary = {"totals": totals, "members": summary}

    print("ending starting all member interest sharing", assist.get_current_date(False))

    return JSONResponse(content=fullSummary, status_code=200)


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
                "name": f"{tran.user.fname} {tran.user.lname}",
                "email": tran.user.email,
                "phone": tran.user.mobile,
                "period": tran.date,
                "type": tran.type.type_name,
                "amount": tran.amount,
            }
        )

    return summary


@router.post("/initialize-validation-savings")
async def initialize_validation_savings(db: AsyncSession = Depends(get_db)):

    try:
        base = os.path.dirname(__file__)
        path = os.path.join(base, "validation-data.xlsx")
        df = pd.read_excel(path, sheet_name="Savings")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to initialize savings. Cannot open validation file': f{e}",
        )

    for row_index, row in df.iterrows():

        month = 1
        member = row_index + 1

        pad = str(member).zfill(3)

        for col_name, value in row.items():
            # skip user id column
            if col_name == "UserID":
                continue

            date = datetime(2025, month, 15)
            # print(row_index, col_name, value, date)
            month = month + 1

            # skip savings with Nan or zero
            if np.isnan(value) or value == 0:
                continue

            db_tran = TransactionDB(
                # id
                type_id=assist.TRANSACTION_SAVINGS,
                penalty_type_id=None,
                # user
                user_id=member,
                # transaction
                date=date,
                source_id=1,
                amount=0 if np.isnan(value) else value,
                comments=None,
                reference=None,
                # loan
                term_months=None,
                interest_rate=None,
                # loan payment transaction id
                parent_id=None,
                # approval
                status_id=assist.STATUS_APPROVED,
                state_id=assist.STATE_CLOSED,
                stage_id=assist.APPROVAL_STAGE_APPROVED,
                approval_levels=2,
                # service
                created_by=f"member-{pad}.acount@gmail.com",
            )
            db.add(db_tran)

        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Unable to initialize transaction for {member}: f{e}",
            )

        # break

    return {
        "succeeded": True,
        "message": "Savings have been successfully initialized",
    }


@router.post("/initialize-validation-loans")
async def initialize_validation_loans(db: AsyncSession = Depends(get_db)):

    try:
        base = os.path.dirname(__file__)
        path = os.path.join(base, "validation-data.xlsx")
        df = pd.read_excel(path, sheet_name="Loans")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to initialize loans. Cannot open validation file': f{e}",
        )

    for row_index, row in df.iterrows():

        month = 1
        member = row_index + 1

        pad = str(member).zfill(3)

        for col_name, value in row.items():
            # skip user id column
            if col_name == "UserID":
                continue

            date = datetime(2025, month, 15)
            # print(row_index, col_name, value, date)
            month = month + 1

            # skip loans with Nan or zero
            if np.isnan(value) or value == 0:
                continue

            db_tran = TransactionDB(
                # id
                type_id=assist.TRANSACTION_LOAN,
                penalty_type_id=None,
                # user
                user_id=member,
                # transaction
                date=date,
                source_id=1,
                amount=0 if np.isnan(value) else value,
                comments=None,
                reference=None,
                # loan
                term_months=None,
                interest_rate=None,
                # loan payment transaction id
                parent_id=None,
                # approval
                status_id=assist.STATUS_APPROVED,
                state_id=assist.STATE_CLOSED,
                stage_id=assist.APPROVAL_STAGE_APPROVED,
                approval_levels=2,
                # service
                created_by=f"member-{pad}.acount@gmail.com",
            )
            db.add(db_tran)

        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Unable to initialize transaction for {member}: f{e}",
            )

        # break

    return {
        "succeeded": True,
        "message": "Loans have been successfully initialized",
    }


@router.post("/initialize-validation-interest")
async def initialize_validation_interest(db: AsyncSession = Depends(get_db)):

    try:
        base = os.path.dirname(__file__)
        path = os.path.join(base, "validation-data.xlsx")
        df = pd.read_excel(path, sheet_name="Interest")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to initialize interest. Cannot open validation file': f{e}",
        )

    for row_index, row in df.iterrows():

        month = 1
        member = row_index + 1

        pad = str(member).zfill(3)

        for col_name, value in row.items():
            # skip user id column
            if col_name == "UserID":
                continue

            date = datetime(2025, month, 15)
            print(row_index, col_name, value, date)
            month = month + 1

            # skip inteerst with Nan or zero
            if np.isnan(value) or value == 0:
                continue

            db_tran = TransactionDB(
                # id
                type_id=assist.TRANSACTION_INTEREST_CHARGED,
                penalty_type_id=None,
                # user
                user_id=member,
                # transaction
                date=date,
                source_id=1,
                amount=0 if np.isnan(value) else value,
                comments=None,
                reference=None,
                # loan
                term_months=None,
                interest_rate=None,
                # loan payment transaction id
                parent_id=None,
                # approval
                status_id=assist.STATUS_APPROVED,
                state_id=assist.STATE_CLOSED,
                stage_id=assist.APPROVAL_STAGE_APPROVED,
                approval_levels=2,
                # service
                created_by=f"member-{pad}.acount@gmail.com",
            )
            db.add(db_tran)

        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Unable to initialize transaction for {member}: f{e}",
            )

        # break

    return {
        "succeeded": True,
        "message": "Interest has been successfully initialized",
    }


@router.post("/initialize-validation-loan-repayment")
async def initialize_validation_loan_repayment(db: AsyncSession = Depends(get_db)):

    try:
        base = os.path.dirname(__file__)
        path = os.path.join(base, "validation-data.xlsx")
        df = pd.read_excel(path, sheet_name="Repayment")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to initialize loan repayment. Cannot open validation file': f{e}",
        )

    for row_index, row in df.iterrows():

        month = 1
        member = row_index + 1

        pad = str(member).zfill(3)

        for col_name, value in row.items():
            # skip user id column
            if col_name == "UserID":
                continue

            date = datetime(2025, month, 15)
            print(row_index, col_name, value, date)
            month = month + 1

            # skip inteerst with Nan or zero
            if np.isnan(value) or value == 0:
                continue

            db_tran = TransactionDB(
                # id
                type_id=assist.TRANSACTION_LOAN_PAYMENT,
                penalty_type_id=None,
                # user
                user_id=member,
                # transaction
                date=date,
                source_id=1,
                amount=0 if np.isnan(value) else value,
                comments=None,
                reference=None,
                # loan
                term_months=None,
                interest_rate=None,
                # loan payment transaction id
                parent_id=None,
                # approval
                status_id=assist.STATUS_APPROVED,
                state_id=assist.STATE_CLOSED,
                stage_id=assist.APPROVAL_STAGE_APPROVED,
                approval_levels=2,
                # service
                created_by=f"member-{pad}.acount@gmail.com",
            )
            db.add(db_tran)

        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Unable to initialize transaction for {member}: f{e}",
            )

        # break

    return {
        "succeeded": True,
        "message": "Loan repayment has been successfully initialized",
    }
