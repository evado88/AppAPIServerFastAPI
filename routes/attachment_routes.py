import io
import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from database import get_db
from helpers import assist
from models.attachment_model import Attachment, AttachmentDB, AttachmentInput
import csv

from models.param_models import ParamAttachmentDetail
from models.user_model import UserDB

router = APIRouter(prefix="/attachments", tags=["Attachment"])


async def validateAttendance(file: UploadFile, db=AsyncSession):

    result = await db.execute(select(UserDB))
    users = result.scalars().all()
    userList = {user.email: "None" for user in users}

    attendanceList = ["In-Person", "Virtual", "Late", "Absent"]

    try:
        contents = await file.read()
        decode_contents = contents.decode("utf-8")

        csv_reader = csv.DictReader(io.StringIO(decode_contents))

        data = list(csv_reader)

        index = 1
        for row in data:
            userMail = row["Email"]
            userAttendance = row["Attendance"]

            if not userAttendance in attendanceList:
                raise HTTPException(
                    status_code=400,
                    detail=f"The attendance type on row {index} '{userAttendance}' is invalid",
                )
            if not userMail in userList.keys():
                raise HTTPException(
                    status_code=400,
                    detail=f"The user on row {index} '{userMail}' does not exist as a member",
                )
            userList[userMail] = userAttendance
            index += 1
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"The attached meeting attendance list file was not found: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process the meeting attendance list: {e}",
        )
        
    listAttendace = [{'user': user.email, "type": userList[user.email]} for user in users]
    return listAttendace


@router.post("/create/type/{typeId}/parent/{parentId}", response_model=ParamAttachmentDetail)
async def post_attachment(
    typeId: str = "Attachment",
    parentId: int = 0,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:

        userList = None
        if typeId == "AttendanceList":
            userList = await validateAttendance(file, db)

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
async def list_attachments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AttachmentDB))
    attachments = result.scalars().all()
    return attachments


@router.get("/{id}", response_model=Attachment)
async def get_attachment(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AttachmentDB).filter(AttachmentDB.id == id))
    attachment = result.scalars().first()
    if not attachment:
        raise HTTPException(
            status_code=404, detail=f"Attachment with id '{id}' not found"
        )
    return attachment
