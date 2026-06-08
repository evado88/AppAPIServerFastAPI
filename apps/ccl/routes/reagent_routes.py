from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy.orm import selectinload
from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.lab_model import LabDB
from apps.ccl.models.param_models import ParamDataImport
from apps.ccl.models.reagent_model import (
    Reagent,
    ReagentDB,
    ReagentParam,
    ReagentWithDetail,
)
from apps.ccl.models.user_model import UserDB
from helpers import assist

router = APIRouter(prefix="/reagents", tags=["Reagents"])


@router.post("/create", response_model=ReagentWithDetail)
async def create(reagent: Reagent, db: AsyncSession = Depends(get_ccl_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == reagent.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{reagent.user_id}' does not exist",
        )

    db_user = ReagentDB(
        # user
        user_id=reagent.user_id,
        # details
        is_control=reagent.is_control,
        name=reagent.name,
        description=reagent.description,
        # costs
        cost=reagent.cost,
        expiry_period=reagent.expiry_period,
        generic_reagent_unit=reagent.generic_reagent_unit,
        quantity_per_gru=reagent.quantity_per_gru,
        tests_per_gru=reagent.tests_per_gru,
        # lists
        lab_list=reagent.lab_list,
        # service
        created_by=user.email,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create reagent: f{e}")
    return db_user


@router.post("/import/{is_control}")
async def import_customers(
    is_control: int,
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
    result = await db.execute(select(ReagentDB))

    existingItems = result.scalars().all()

    index = 0
    added = 0
    updated = 0

    startProcess = assist.get_current_date(False)
    
    title = 'Consumable' if is_control == 1 else 'Reagent' 

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

            itemRecord.name = item["name"]
            itemRecord.description = item["description"]
            itemRecord.cost = item["cost"]
            itemRecord.expiry_period = item["expiry_period"]
            itemRecord.generic_reagent_unit = item["generic_reagent_unit"]
            itemRecord.quantity_per_gru = item["quantity_per_gru"]
            itemRecord.tests_per_gru = item["tests_per_gru"]

            # commit
            try:
                await db.commit()
                await db.refresh(itemRecord)

                updated += 1
            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Unable to update {title}: {e}"
                )
        else:
            # add new item
            db_customer = ReagentDB(
                # user
                user_id=user.id,
                # details
                is_control=True if is_control == 1 else False,
                name=item["name"],
                description=item["description"],
                # costs
                cost=item["cost"],
                expiry_period=item["expiry_period"],
                generic_reagent_unit=item["generic_reagent_unit"],
                quantity_per_gru=item["quantity_per_gru"],
                tests_per_gru=item["tests_per_gru"],
                # lists
                lab_list=[],
                # service
                created_by=user.email,
            )
            db.add(db_customer)
            added += 1

    # commit changes
    try:
        # comit changes
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to import {title}s: f{e}")

    endProcess = assist.get_current_date(False)

    print(f"Import {title} Duration. Start={startProcess}, End={endProcess}")

    return {
        "succeeded": True,
        "message": f"Successfully imported {index} {title}(s). Updated {updated} and added {added} {title}(s)",
    }


@router.get("/id/{reagent_id}", response_model=ReagentParam)
async def get_item(reagent_id: int, db: AsyncSession = Depends(get_ccl_db)):

    reagentItem = None

    # only load reagent if not zero
    if reagent_id != 0:
        result = await db.execute(
            select(ReagentDB)
            .options(
                selectinload(ReagentDB.user),
            )
            .where(ReagentDB.id == reagent_id)
        )
        reagentItem = result.scalars().first()

        if not reagentItem:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to find reagent with id '{reagent_id}'",
            )

    # get labs

    result = await db.execute(
        select(LabDB)
        .options(
            selectinload(LabDB.user),
        )
        .order_by(LabDB.name)
    )
    labList = result.scalars().all()

    # return param
    param = ReagentParam(reagent=reagentItem, labs=labList)

    return param


@router.put("/update/{reagent_id}", response_model=ReagentWithDetail)
async def update_item(
    reagent_id: int,
    reagent_update: Reagent,
    db: AsyncSession = Depends(get_ccl_db),
):
    result = await db.execute(
        select(ReagentDB)
        .options(
            selectinload(ReagentDB.user),
        )
        .where(ReagentDB.id == reagent_id)
    )
    reagent = result.scalar_one_or_none()

    if not reagent:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find reagent with id '{reagent_id}'",
        )

    # Update fields that are not None
    for key, value in reagent_update.dict(exclude_unset=True).items():
        setattr(reagent, key, value)

    try:
        await db.commit()
        await db.refresh(reagent)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update reagent {e}")
    return reagent


@router.get("/list/{is_control}", response_model=List[ReagentWithDetail])
async def list_items(is_control: int, db: AsyncSession = Depends(get_ccl_db)):
    control = False if is_control == 0 else True
    result = await db.execute(
        select(ReagentDB)
        .options(
            selectinload(ReagentDB.user),
        )
        .where(ReagentDB.is_control == control)
        .order_by(ReagentDB.name)
    )
    return result.scalars().all()
