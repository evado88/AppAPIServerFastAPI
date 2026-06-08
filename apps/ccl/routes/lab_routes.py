from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy.orm import selectinload
from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.lab_model import Lab, LabDB, LabItem, LabWithDetail
from apps.ccl.models.param_models import ParamDataImport
from apps.ccl.models.user_model import UserDB
from helpers import assist

router = APIRouter(prefix="/labs", tags=["Labs"])


@router.post("/create", response_model=LabWithDetail)
async def create_item(lab: Lab, db: AsyncSession = Depends(get_ccl_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == lab.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{lab.user_id}' does not exist"
        )

    db_user = LabDB(
        # user
        user_id=lab.user_id,
        # details
        name=lab.name,
        description=lab.description,
        # service
        created_by=user.email,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create lab: f{e}")
    return db_user


@router.post("/import")
async def import_customers(
    dataImport: ParamDataImport,
    db: AsyncSession = Depends(get_ccl_db),
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == dataImport.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{dataImport.user_id}' does not exist",
        )

    # existig labs
    result = await db.execute(select(LabDB))

    existingItems = result.scalars().all()

    index = 0
    added = 0
    updated = 0

    startProcess = assist.get_current_date(False)

    for item in dataImport.items:

        # update count
        index += 1

        # get name
        name = item["name"]

        # keep track of items that exist
        itemRecord = next((c for c in existingItems if c.name == name), None)
        itemExists = itemRecord is not None

        if itemExists:

            # update available fields
            for key in item.keys():
                if not key == "no":
                    setattr(itemRecord, key, item[key])

            # commit
            try:
                await db.commit()
                await db.refresh(itemRecord)

                updated += 1
            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Unable to update lab: {e}"
                )
        else:
            # add new item
            data = {key: item[key] for key in item.keys() if not key == "no"}
            
            db_customer = LabDB(
                # user
                user_id=user.id,
                # service
                created_by=user.email,
                **data
            )
            db.add(db_customer)
            added += 1

    # commit changes
    try:
        # comit changes
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to import labs: f{e}")

    endProcess = assist.get_current_date(False)

    print(f"Import Lab Duration. Start={startProcess}, End={endProcess}")

    return {
        "succeeded": True,
        "message": f"Successfully imported {index} lab(s). Updated {updated} and added {added} lab(s)",
    }


@router.get("/id/{lab_id}", response_model=LabWithDetail)
async def get_item(lab_id: int, db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(LabDB)
        .options(
            selectinload(LabDB.user),
        )
        .where(LabDB.id == lab_id)
        .order_by(LabDB.name)
    )

    lab = result.scalars().first()
    if not lab:
        raise HTTPException(
            status_code=404, detail=f"Unable to find lab with id '{lab_id}'"
        )
    return lab


@router.put("/update/{lab_id}", response_model=LabWithDetail)
async def update_item(
    lab_id: int, lab_update: Lab, db: AsyncSession = Depends(get_ccl_db)
):
    result = await db.execute(
        select(LabDB)
        .options(
            selectinload(LabDB.user),
        )
        .where(LabDB.id == lab_id)
        .order_by(LabDB.name)
    )

    lab = result.scalar_one_or_none()

    if not lab:
        raise HTTPException(
            status_code=404, detail=f"Unable to find lab with id '{lab_id}'"
        )

    # Update fields that are not None
    for key, value in lab_update.dict(exclude_unset=True).items():
        setattr(lab, key, value)

    try:
        await db.commit()
        await db.refresh(lab)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update lab {e}")
    return lab


@router.get("/list", response_model=List[LabWithDetail])
async def list(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(LabDB)
        .options(
            selectinload(LabDB.user),
        )
        .order_by(LabDB.name)
    )
    return result.scalars().all()


@router.get("/items", response_model=List[LabItem])
async def list_items(db: AsyncSession = Depends(get_ccl_db)):
    result = await db.execute(
        select(LabDB)
        .options(
            selectinload(LabDB.user),
        )
        .order_by(LabDB.name)
    )
    return result.scalars().all()
