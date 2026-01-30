from datetime import datetime, timedelta, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from jose import JWTError, jwt
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.configuration_model import AppConfigurationDB
from apps.lwsc.models.user_model import User, UserDB
import helpers.assist as assist
from apps.lwsc.models.whatsapp_models import AuthParam, MobileParam, ItemReviewParam, TransactionReviewParam
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
