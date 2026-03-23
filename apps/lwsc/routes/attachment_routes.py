import io
import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.customer_model import CustomerDB
from apps.osawe.models.member_model import MemberDB
from helpers import assist
from apps.lwsc.models.attachment_model import Attachment, AttachmentDB, AttachmentInput
import csv


from apps.lwsc.models.param_models import ParamAttachmentDetail
from apps.lwsc.models.user_model import UserDB

router = APIRouter(prefix="/attachments", tags=["Attachment"])


async def processCustomers(file: UploadFile, db=AsyncSession):

    # list
    newCustomers = []

    try:
        contents = await file.read()
        decode_contents = contents.decode("utf-8-sig")

        csv_reader = csv.DictReader(io.StringIO(decode_contents))

        data = list(csv_reader)

        index = 1

        keys = [
            "Account",
            "Current",
            "Previous",
            "Remarks",
            "Meter",
            "StreetName",
            "StreetNo",
            "Dept",
            "ConsCode",
            "Ward",
            "Suburb",
            "Name",
            "Latitude",
            "Longitude",
        ]

        for row in data:
            customer = {}

            for key in keys:
                if (
                    key == "Latitude"
                    or key == "Longitude"
                    or key == "Current"
                    or key == "Previous"
                ):
                    customer[key] = float(row[key])
                else:
                    customer[key] = row[key]

            newCustomers.append(customer)

            index += 1

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"The attached customer import list file was not found: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process the customer import list file: {e}",
        )

    return newCustomers


async def processBillRates(file: UploadFile, db=AsyncSession):

    # list
    newRates = []

    try:
        contents = await file.read()
        decode_contents = contents.decode("utf-8-sig")

        csv_reader = csv.DictReader(io.StringIO(decode_contents))

        data = list(csv_reader)

        index = 1

        keys = [
            "Order",
            "Name",
            "From",
            "To",
            "Rate",
        ]

        for row in data:
            billRate = {}

            for key in keys:
                if key == "Rate" or key == "From" or key == "To":
                    billRate[key] = float(row[key])
                elif key == "OrderName":
                    billRate[key] = int(row[key])
                else:
                    billRate[key] = row[key]

            newRates.append(billRate)

            index += 1

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"The attached bill rate list file was not found: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process the bill rate list: {e}",
        )

    return newRates


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

        itemList = []

        if typeId == "customerImport":
            itemList = await processCustomers(file, db)
        elif typeId == "billRateImport":
            itemList = await processBillRates(file, db)
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

        # return response
        param = {
            "attachment": db_attachment,
            "items": itemList,
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
