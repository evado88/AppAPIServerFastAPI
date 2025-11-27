import io
import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from helpers import assist
from models.attachment_model import Attachment, AttachmentDB, AttachmentInput
import csv

from models.configuration_model import SACCOConfigurationDB
from models.member_model import MemberDB
from models.param_models import ParamAttachmentDetail
from models.user_model import UserDB

router = APIRouter(prefix="/attachments", tags=["Attachment"])


async def validateAttendance(file: UploadFile, db=AsyncSession):

    result = await db.execute(
        select(SACCOConfigurationDB).filter(SACCOConfigurationDB.id == 1)
    )

    config = result.scalars().first()

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to process meeting: Configuration with id '{1}' not found",
        )

    result = await db.execute(
        select(MemberDB).where(MemberDB.status_id == assist.STATUS_APPROVED)
    )
    members = result.scalars().all()

    # absent is the default
    memberList = {
        mem.email: {
            "Id": mem.user_id,
            "Type": "Absent",
            "TypeId": 4,
            "Penalty": config.missed_meeting_rate,
            "PenaltyId": 2,
        }
        for mem in members
    }

    attendanceList = {
        "In-Person": None,
        "Virtual": None,
        "Late": assist.PENALTY_LATE_MEETING,
        "Absent": assist.PENALTY_MISSED_MEETING,
    }

    penaltyFeeList = {
        "In-Person": 0.0,
        "Virtual": 0.0,
        "Late": config.late_meeting_rate,
        "Absent": config.missed_meeting_rate,
    }
    
    penaltyIdList = {
        "In-Person": None,
        "Virtual": None,
        "Late": assist.PENALTY_LATE_MEETING,
        "Absent": assist.PENALTY_MISSED_MEETING,
    }
    
    try:
        contents = await file.read()
        decode_contents = contents.decode("utf-8")

        csv_reader = csv.DictReader(io.StringIO(decode_contents))

        data = list(csv_reader)

        index = 1

        for row in data:
            userMail = row["Email"]
            userAttendance = row["Attendance"]

            if not userAttendance in attendanceList.keys():
                raise HTTPException(
                    status_code=400,
                    detail=f"The attendance type on row {index} '{userAttendance}' is invalid",
                )
            elif userAttendance == "Absent":
                raise HTTPException(
                    status_code=400,
                    detail=f"The attendance on row {index} is invalid. Absent members should not be included",
                )
            

            if not userMail in memberList.keys():
                raise HTTPException(
                    status_code=400,
                    detail=f"The user on row {index} '{userMail}' does not exist as a member",
                )

            memberList[userMail]["Type"] = userAttendance
            memberList[userMail]["TypeId"] = attendanceList[userAttendance]
            memberList[userMail]["Penalty"] = penaltyFeeList[userAttendance]
            memberList[userMail]["PenaltyId"] = penaltyIdList[userAttendance]
            
            index += 1

        listAttendace = [
            {
                "id": memberList[user.email]["Id"],
                "user": user.email,
                "type": memberList[user.email]["Type"],
                "typeId": memberList[user.email]["TypeId"],
                "penalty": memberList[user.email]["Penalty"],
                "penaltyId": memberList[user.email]["PenaltyId"],
            }
            for user in members
        ]
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

    return listAttendace


@router.post(
    "/create/type/{typeId}/parent/{parentId}", response_model=ParamAttachmentDetail
)
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
