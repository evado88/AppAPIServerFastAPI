from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.lwsc import lwscapp
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.meters_model import (
    Meters,
    MetersWithDetail,
    ParamMetersEdit,
    MetersDB,
)

# approval
from apps.lwsc.models.param_models import ParamMetersImport
from apps.lwsc.models.review_model import AppReview
from apps.lwsc.models.user_model import User, UserDB
from helpers import assist
from sqlalchemy.orm import selectinload

# relations

router = APIRouter(prefix="/meters", tags=["Meterss"])


@router.post("/create", response_model=Meters)
async def post_meters(meters: Meters, db: AsyncSession = Depends(get_lwsc_db)):

    db_context = MetersDB(
        # properties
        customer_number=meters.customer_number,
        customer_name=meters.customer_name,
        identity_number=meters.identity_number,
        address=meters.address,
        communicate_address=meters.communicate_address,
        invoice_number=meters.invoice_number,
        open_account_date=meters.open_account_date,
        station_name=meters.station_name,
        operator_uid=meters.operator_uid,
        province_name=meters.province_name,
        city_name=meters.city_name,
        town_name=meters.town_name,
        village_name=meters.village_name,
        # approval
        user_id=meters.user_id,
        status_id=meters.status_id,
        stage_id=meters.stage_id,
        approval_levels=meters.approval_levels,
        # service
        created_by=meters.created_by,
    )
    db.add(db_context)
    try:
        await db.commit()
        await db.refresh(db_context)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not create Meter: {e}")

    return db_context


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):

    itemList = []

    for value in itemList:
        db_item = MetersDB(
            # add item
            name=value["name"],
            user_id=1,
            status_id=4,
            stage_id=5,
            approval_levels=1,
        )
        db.add(db_item)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to initialize items for Meter: f{e}"
        )
    return {
        "succeeded": True,
        "message": "Items for Meter have been successfully initialized",
    }


@router.get("/list", response_model=List[MetersWithDetail])
async def list_meterss(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(MetersDB).options(
            selectinload(MetersDB.stage),
            selectinload(MetersDB.status),
            selectinload(MetersDB.user),
        )
    )
    meterss = result.scalars().all()
    return meterss


@router.put("/update/{id}", response_model=Meters)
async def update_meters(
    id: int, meters_update: Meters, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(select(MetersDB).where(MetersDB.id == id))
    meters = result.scalar_one_or_none()

    if not meters:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find Meter with id '{id}'",
        )

    # Update fields that are not None
    for key, value in meters_update.dict(exclude_unset=True).items():
        setattr(meters, key, value)

    try:
        await db.commit()
        await db.refresh(meters)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update Meter {e}")
    return meters


@router.post("/import")
async def import_customers(
    meterImport: ParamMetersImport,
    db: AsyncSession = Depends(get_lwsc_db),
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == meterImport.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{meterImport.user_id}' does not exist",
        )

    # existig meters
    result = await db.execute(
        select(MetersDB).where(MetersDB.status_id == assist.STATUS_APPROVED)
    )

    existingMeters = result.scalars().all()

    index = 0
    added = 0
    updated = 0

    startProcess = assist.get_current_date(False)

    for meter in meterImport.items:

        # update count
        index += 1

        # get account number
        account = meter["CustomerNumber"]

        # keep track if customers who exist
        meterExists = False
        meterRecord = None

        for c in existingMeters:
            if c.customer_number == account:
                meterExists = True
                meterRecord = c
                break

        if meterExists:
            # update customer available fields

            meterRecord.customer_number = meter["CustomerNumber"]
            meterRecord.customer_name = meter["CustomerName"]
            meterRecord.identity_number = meter["IdentityNumber"]
            meterRecord.address = meter["Address"]
            meterRecord.communicate_address = meter["CommunicateAddress"]
            meterRecord.invoice_number = meter["InvoiceNumber"]
            meterRecord.open_account_date = meter["OpenAccountDate"]
            meterRecord.station_name = meter["StationName"]
            meterRecord.operator_uid = meter["OperatorUID"]
            meterRecord.province_name = meter["ProvinceName"]
            meterRecord.city_name = meter["CityName"]
            meterRecord.town_name = meter["TownName"]
            meterRecord.village_name = meter["VillageName"]

            # commit
            try:
                await db.commit()
                await db.refresh(meterRecord)

                updated += 1
            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Unable to update customer {e}"
                )
        else:
            # add customer
            db_customer = MetersDB(
                # user
                user_id=meterImport.user_id,
                # detail
                customer_number=meter["CustomerNumber"],
                customer_name=meter["CustomerName"],
                identity_number=meter["IdentityNumber"],
                address=meter["Address"],
                communicate_address=meter["CommunicateAddress"],
                invoice_number=meter["InvoiceNumber"],
                open_account_date=meter["OpenAccountDate"],
                station_name=meter["StationName"],
                operator_uid=meter["OperatorUID"],
                province_name=meter["ProvinceName"],
                city_name=meter["CityName"],
                town_name=meter["TownName"],
                village_name=meter["VillageName"],
                # approval
                status_id=lwscapp.STATUS_APPROVED,
                stage_id=lwscapp.APPROVAL_STAGE_APPROVED,
                approval_levels=1,
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
        raise HTTPException(status_code=400, detail=f"Unable to import meters: f{e}")

    endProcess = assist.get_current_date(False)

    print(f"Import Duration. Start={startProcess}, End={endProcess}")

    return {
        "succeeded": True,
        "message": f"Successfully imported {index} meter(s). Updated {updated} and added {added} meter(s)",
    }


@router.get("/id/{id}", response_model=ParamMetersEdit)
async def get_meters(id: int, db: AsyncSession = Depends(get_lwsc_db)):
    metersItem = None
    # only load if not zero
    if id != 0:
        result = await db.execute(
            select(MetersDB)
            .options(
                selectinload(MetersDB.stage),
                selectinload(MetersDB.status),
                selectinload(MetersDB.user),
            )
            .filter(MetersDB.id == id)
        )
        metersItem = result.scalars().first()
        if not metersItem:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to find 'Meter with id '{id}' not found",
            )

    # get supporting models if available

    res = ParamMetersEdit(
        meters=metersItem,
    )

    return res

@router.get("/acccount/{account}", response_model=Meters)
async def get_meter_account(account: str, db: AsyncSession = Depends(get_lwsc_db)):
    metersItem = None
    # only load if not zero

    result = await db.execute(
        select(MetersDB)
        .options(
            selectinload(MetersDB.stage),
            selectinload(MetersDB.status),
            selectinload(MetersDB.user),
        )
        .filter(MetersDB.communicate_address == account)
    )
    metersItem = result.scalars().first()
    if not metersItem:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find Meter with number '{account}'",
        )

    return metersItem



@router.put("/review-update/{id}", response_model=Meters)
async def review_posting(
    id: int, review: AppReview, db: AsyncSession = Depends(get_lwsc_db)
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == review.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{review.user_id}' does not exist",
        )

    # check if item exists
    result = await db.execute(select(MetersDB).where(MetersDB.id == id))
    meters = result.scalar_one_or_none()

    if not meters:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find Meter with id '{id}' not found",
        )

    if meters.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The Meter with id '{id}' has already been approved",
        )

    meters.updated_by = user.email

    approveMeters = False

    if meters.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        if meters.user_id == user.id:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the first reviewer of a Meter you created",
            )

        meters.review1_at = assist.get_current_date(False)
        meters.review1_by = user.email
        meters.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            meters.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if meters.approval_levels == 1:
                # one level, no furthur stage approvers

                # approve meters
                approveMeters = True

            elif meters.approval_levels == 2 or meters.approval_levels == 3:
                # two or three levels, move to primary

                meters.stage_id = assist.APPROVAL_STAGE_PRIMARY

    elif meters.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage

        if meters.review1_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the secondary reviewer since you were the primary reviewer",
            )

        meters.review2_at = assist.get_current_date(False)
        meters.review2_by = user.email
        meters.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            meters.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if meters.approval_levels == 2:
                # two levels, no furthur stage approvers

                approveMeters = True

            elif meters.approval_levels == 3:
                # three levels, move to secondary
                meters.stage_id = assist.APPROVAL_STAGE_SECONDARY

    elif meters.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage

        if meters.review2_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the final reviewer since you were the secondary reviewer",
            )

        meters.review3_at = assist.get_current_date(False)
        meters.review3_by = user.email
        meters.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            meters.status_id = assist.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage
            approveMeters = True

    if approveMeters:
        # change meters status
        meters.status_id = assist.STATUS_APPROVED
        meters.stage_id = assist.APPROVAL_STAGE_APPROVED

        # attachment may or may not be provided

    try:
        await db.commit()
        await db.refresh(meters)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update Meter: {e}")
    return meters
