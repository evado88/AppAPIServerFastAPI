import io
import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.ccl import importassist
from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.attachment_model import Attachment, AttachmentDB
from helpers import assist
import csv


from apps.lwsc.models.param_models import ParamAttachmentDetail
from apps.lwsc.models.user_model import UserDB

router = APIRouter(prefix="/attachments", tags=["Attachment"])


async def processImport(file: UploadFile, fields: List, title: str):

    # list
    try:
        contents = await file.read()
        decode_contents = contents.decode("utf-8-sig")

        csv_reader = csv.DictReader(io.StringIO(decode_contents))

        # Get the list of available columns from the CSV
        available_columns = csv_reader.fieldnames or []

        # validate columns before reading even starts
        for field in fields:
            if not field["name"] in available_columns:
                raise HTTPException(
                    status_code=500,
                    detail=f"The column '{field['name']}' is required but does not exist in the CSV file. Please check template",
                )

        data = list(csv_reader)

        index = 1

        newRows = []

        for row in data:

            if not any(value and value.strip() for value in row.values()):
                continue

            rowItem = {}

            # add fields
            rowItem["no"] = index

            for field in fields:
                if field["dataType"] == "float":
                    rowItem[field["id"]] = float(row[field["name"]])
                elif field["dataType"] == "int":
                    rowItem[field["id"]] = int(row[field["name"]])
                else:
                    rowItem[field["id"]] = row[field["name"]]

            newRows.append(rowItem)

            index += 1

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"The attached {title} import list file was not found: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process the {title} import list file: {e}",
        )

    return newRows


async def processLabs(file: UploadFile):
    return await processImport(file, importassist.labFields, "Labs")


async def processReagents(file: UploadFile):
    return await processImport(file, importassist.reagentFields, "Reagents")


async def processInstruments(file: UploadFile):
    return await processImport(file, importassist.instrumentFields, "Instruments")


async def processTests(file: UploadFile):
    return await processImport(file, importassist.testFields, "Tests")


async def processTestPriceVolume(file: UploadFile):
    return await processImport(
        file, importassist.testPriceVolumeFields, "Test Price Volume"
    )


@router.post(
    "/create/type/{typeId}/parent/{parentId}", response_model=ParamAttachmentDetail
)
async def post_attachment(
    typeId: str = "Attachment",
    parentId: int = 0,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_ccl_db),
):
    try:

        itemList = []

        if typeId == "importLabs":
            itemList = await processLabs(file)
        elif typeId == "importReagents":
            itemList = await processReagents(file)
        elif typeId == "importConsumables":
            itemList = await processReagents(file)
        elif typeId == "importInstruments":
            itemList = await processInstruments(file)
        elif typeId == "importTests":
            itemList = await processTests(file)
        elif typeId == "importTestPriceVolume":
            itemList = await processTestPriceVolume(file)
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
        param = ParamAttachmentDetail(attachment=db_attachment, items=itemList)

        return param

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.get("/list", response_model=List[Attachment])
async def list_attachments(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(AttachmentDB))
    attachments = result.scalars().all()
    return attachments


@router.get("/{id}", response_model=Attachment)
async def get_attachment(id: int, db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(select(AttachmentDB).where(AttachmentDB.id == id))
    attachment = result.scalars().first()
    if not attachment:
        raise HTTPException(
            status_code=404, detail=f"Attachment with id '{id}' not found"
        )
    return attachment
