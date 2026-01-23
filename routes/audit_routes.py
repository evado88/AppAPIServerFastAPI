import os
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy import select, desc
from database import get_db
from helpers import assist
from models.attachment_model import AttachmentDB
from models.audit_model import Audit, AuditDB, AuditSimpleWithDetail, AuditWithDetail
from models.review_model import SACCOReview
from models.transaction_model import TransactionDB
from models.user_model import UserDB
import json

router = APIRouter(prefix="/audits", tags=["Audits"])


@router.post("/create", response_model=Audit)
async def post_audit(audit: Audit, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == audit.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"User with id {audit.user_id} does not exist"
        )

    db_tran = AuditDB(
        # user
        user_id=audit.user_id,
        user_email=audit.user_email,
        token=audit.token,
        # audit
        date=audit.date,
        feature=audit.feature,
        object_id=audit.object_id,
        action=audit.action,
        before=audit.before,
        after=audit.after,
        # service
        created_by=user.email,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not create audit: {e}")

    return db_tran


@router.get("/list", response_model=List[AuditSimpleWithDetail])
async def list_audits(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuditDB).order_by(desc(AuditDB.created_at)).limit(50)
    )
    audits = result.scalars().all()
    return audits


@router.get("/id/{audit_id}", response_model=AuditWithDetail)
async def get_audit(audit_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditDB).filter(AuditDB.id == audit_id))
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(
            status_code=404, detail=f"Audit with id '{audit_id}' not found"
        )

    return audit
