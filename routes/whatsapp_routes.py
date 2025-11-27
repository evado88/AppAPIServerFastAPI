from datetime import datetime, timedelta, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from jose import JWTError, jwt
from database import get_db
from models.configuration_model import SACCOConfigurationDB
from models.member_model import MemberDB
from models.monthly_post_model import MonthlyPostingDB
from models.transaction_model import TransactionDB
from models.user_model import User, UserDB
import helpers.assist as assist
from models.whatsapp_models import AuthParam, MobileParam, ItemReviewParam, TransactionReviewParam
from helpers.http_client import get_http_client
from sqlalchemy import or_

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.post("/send-infobip-auth-message")
async def send_auth_message(param: AuthParam):

    messageId = uuid.uuid4()

    headers = {
        "Authorization": f"App {assist.INFOBIP_API_TOKEN}",
        "Content-type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "messages": [
            {
                "from": assist.INFOBIP_PHONE_NUMBER,
                "to": param.mobile,
                "messageId": str(messageId),
                "content": {
                    "templateName": "auth",
                    "templateData": {
                        "body": {"placeholders": [f"{param.code}"]},
                        "buttons": [{"type": "URL", "parameter": "Copy"}],
                    },
                    "language": "en",
                },
            }
        ]
    }

    client = get_http_client()

    response = await client.post(assist.INFOBIP_API_URL, json=data, headers=headers)

    return {"status": response.status_code, "data": response.json()}


@router.post("/send-infobip-register-message")
async def send_account_registered(
    param: ItemReviewParam, db: AsyncSession = Depends(get_db)
):
    # check user exists
    result = await db.execute(select(MemberDB).where(MemberDB.id == param.id))
    member = result.scalars().first()

    # check if this person has registered as a member
    if not member:
        # not registered
        raise HTTPException(
            status_code=401,
            detail=f"The specified member id'{param.id}' is incorrect",
        )

    messageId = uuid.uuid4()

    headers = {
        "Authorization": f"App {assist.INFOBIP_API_TOKEN}",
        "Content-type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "messages": [
            {
                "from": assist.INFOBIP_PHONE_NUMBER,
                "to": f"+{member.mobile1}",
                "messageId": str(messageId),
                "content": {
                    "templateName": "account_received",
                    "templateData": {
                        "body": {"placeholders": [f"{member.fname}"]},
                    },
                    "language": "en_GB",
                },
            }
        ]
    }

    client = get_http_client()

    response = await client.post(assist.INFOBIP_API_URL, json=data, headers=headers)

    return {"status": response.status_code, "data": response.json()}


@router.post("/send-infobip-account-approved-message")
async def send_account_approved(param: ItemReviewParam, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(MemberDB).where(MemberDB.id == param.id))
    member = result.scalars().first()

    # check if this person has registered as a member
    if not member:
        # not registered
        raise HTTPException(
            status_code=401,
            detail=f"The specified member id '{param.id}' is incorrect",
        )

    messageId = uuid.uuid4()

    headers = {
        "Authorization": f"App {assist.INFOBIP_API_TOKEN}",
        "Content-type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "messages": [
            {
                "from": assist.INFOBIP_PHONE_NUMBER,
                "to": f"+{member.mobile1}",
                "messageId": str(messageId),
                "content": {
                    "templateName": "account_approved",
                    "templateData": {
                        "body": {"placeholders": [f"{member.fname}"]},
                    },
                    "language": "en_GB",
                },
            }
        ]
    }

    client = get_http_client()

    response = await client.post(assist.INFOBIP_API_URL, json=data, headers=headers)

    return {"status": response.status_code, "data": response.json()}


@router.get("/send-infobip-posting-reminder-messages")
async def send_posting_reminder_messages(db: AsyncSession = Depends(get_db)):
    # get config
    result = await db.execute(
        select(SACCOConfigurationDB).filter(SACCOConfigurationDB.id == 1)
    )

    config = result.scalars().first()
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to load param: Configuration with id '{1}' not found",
        )

    # get all members who have not been reminded today
    current = assist.get_current_date()

    day = config.late_posting_date_start.strftime("%d")
    month = current.strftime("%B %Y")

    period = f"{day} {month}"

    result = await db.execute(
        select(MemberDB)
        .where(
            or_(
                MemberDB.last_reminder_date.is_(None),
                MemberDB.last_reminder_date != current,
            )
        )
        .limit(3)
        .order_by(MemberDB.id)
    )
    members = result.scalars().all()

    # check if this person has registered as a member
    if len(members) == 0:
        # not registered
        raise HTTPException(
            status_code=401,
            detail=f"There no members to send reminders to for the current date",
        )

    index = 0

    for mem in members:

        messageId = uuid.uuid4()

        headers = {
            "Authorization": f"App {assist.INFOBIP_API_TOKEN}",
            "Content-type": "application/json",
            "Accept": "application/json",
        }

        data = {
            "messages": [
                {
                    "from": assist.INFOBIP_PHONE_NUMBER,
                    "to": f"+{mem.mobile1}",
                    "messageId": str(messageId),
                    "content": {
                        "templateName": "posting_reminder",
                        "templateData": {
                            "body": {"placeholders": [f"{mem.fname}", f"{period}"]},
                        },
                        "language": "en_GB",
                    },
                }
            ]
        }

        client = get_http_client()

        response = await client.post(assist.INFOBIP_API_URL, json=data, headers=headers)

        # check if response succeeded
        if response.status_code == 200:
            # update current member
            mem.last_reminder_date = current
            index += 1

            try:
                await db.commit()
                await db.refresh(mem)
            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Unable to update member last reminder details: {e}",
                )

    return {
        "succeeded": True,
        "message": f"Successfully sent messages to {index} member(s) from a total of {len(members)} member(s)",
    }


@router.post("/send-infobip-posting-reviewed-message")
async def send_posting_reviewed(
    param: ItemReviewParam, db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(MonthlyPostingDB).where(MonthlyPostingDB.id == param.id)
    )
    posting = result.scalar_one_or_none()

    if not posting:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find monthly posting with id '{param.id}'",
        )

    # check user exists
    result = await db.execute(select(MemberDB).where(MemberDB.id == posting.member_id))
    member = result.scalars().first()

    # check if this person has registered as a member
    if not member:
        # not registered
        raise HTTPException(
            status_code=401,
            detail=f"The specified member id '{posting.member_id}' is incorrect",
        )
        
    period = posting.date.strftime("%B %Y")

    messageId = uuid.uuid4()

    headers = {
        "Authorization": f"App {assist.INFOBIP_API_TOKEN}",
        "Content-type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "messages": [
            {
                "from": assist.INFOBIP_PHONE_NUMBER,
                "to": f"+{member.mobile1}",
                "messageId": str(messageId),
                "content": {
                    "templateName": "posting_reviewed",
                    "templateData": {
                        "body": {
                            "placeholders": [
                                f"{member.fname}",
                                f"{period}",
                                f"{param.action}",
                            ]
                        },
                    },
                    "language": "en_GB",
                },
            }
        ]
    }

    client = get_http_client()

    response = await client.post(assist.INFOBIP_API_URL, json=data, headers=headers)

    return {"status": response.status_code, "data": response.json()}

@router.post("/send-infobip-transaction-reviewed-message")
async def send_transaction_reviewed(
    param: TransactionReviewParam, db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(TransactionDB).where(TransactionDB.id == param.id)
    )
    transation = result.scalar_one_or_none()

    if not transation:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find transaction with id '{param.id}'",
        )

    # check user exists
    result = await db.execute(select(MemberDB).where(MemberDB.id == transation.member_id))
    member = result.scalars().first()

    # check if this person has registered as a member
    if not member:
        # not registered
        raise HTTPException(
            status_code=401,
            detail=f"The specified member id '{transation.member_id}' is incorrect",
        )
        
    period = transation.date.strftime("%B %Y")

    messageId = uuid.uuid4()

    headers = {
        "Authorization": f"App {assist.INFOBIP_API_TOKEN}",
        "Content-type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "messages": [
            {
                "from": assist.INFOBIP_PHONE_NUMBER,
                "to": f"+{member.mobile1}",
                "messageId": str(messageId),
                "content": {
                    "templateName": "transaction_reviewed",
                    "templateData": {
                        "body": {
                            "placeholders": [
                                f"{member.fname}",
                                f"{param.type}",
                                f"{param.amount}",
                                f"{param.action}",
                            ]
                        },
                    },
                    "language": "en_GB",
                },
            }
        ]
    }

    client = get_http_client()

    response = await client.post(assist.INFOBIP_API_URL, json=data, headers=headers)

    return {"status": response.status_code, "data": response.json()}
