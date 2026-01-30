import io
import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.lwsc.lwscdb import get_lwsc_db
from helpers import assist
from apps.lwsc.models.attachment_model import Attachment, AttachmentDB, AttachmentInput
import csv


from apps.lwsc.models.param_models import ParamAttachmentDetail
from apps.lwsc.models.user_model import UserDB

router = APIRouter(prefix="/attachments", tags=["Attachment"])



@router.post(
    "/create/type/{typeId}/parent/{parentId}", response_model=ParamAttachmentDetail
)
async def post_attachment(
    typeId: str = "Attachment",
    parentId: int = 0,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_lwsc_db),
):
    try:

        userList = None

        # ensure folders exist
        current = assist.get_current_date()
        dir = f"{assist.UPLOAD_DIR}/{current.year}/{current.month}"

        os.makedirs(dir, exist_ok=True)

        # Validate filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Generate unique name
        fileDetail = os.path.splitext(file.filename)
        noextensionfile = fileDetail[0]
        ext = fileDetail[1]

        unique_name = f"{noextensionfile}_{uuid.uuid4()}{ext}"
        file_path = os.path.join(dir, unique_name)

        # Save file safely
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        # update file
        db_attachment = AttachmentDB(
            # personal details
            name=file.filename,
            path=f"{current.year}/{current.month}/{unique_name}",
            filesize=len(contents),
            filetype=file.content_type,
            type=typeId,
            parent=parentId,
        )

        db.add(db_attachment)
        await db.commit()
        await db.refresh(db_attachment)

        # rerturn response
        param = {
            "attachment": db_attachment,
            "attendance": userList,
        }

        return param

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.get("/list", response_model=List[Attachment])
async def list_attachments(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(AttachmentDB))
    attachments = result.scalars().all()
    return attachments


@router.get("/{id}", response_model=Attachment)
async def get_attachment(id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(AttachmentDB).filter(AttachmentDB.id == id))
    attachment = result.scalars().first()
    if not attachment:
        raise HTTPException(
            status_code=404, detail=f"Attachment with id '{id}' not found"
        )
    return attachment
