from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy.orm import selectinload, load_only
from apps.lwsc import lwscapp
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.district_model import DistrictDB
from apps.lwsc.models.param_models import ParamCustomerImport, ParamUserEdit
from apps.lwsc.models.reader_walkroute_model import (
    MeterReaderWalkRouteDB,
    MeterReaderWalkRouteWithDetail,
)
from apps.lwsc.models.walkroute_model import (
    WalkRouteDB,
    WalkRouteItem,
    WalkRouteWithSimpleDetail,
)
from helpers import assist
from helpers import validation
from apps.lwsc.models.review_model import AppReview
from apps.lwsc.models.user_model import User, UserDB, UserSimple, UserWithDetail

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/create", response_model=User)
async def create_user(user: User, db: AsyncSession = Depends(get_lwsc_db)):
    # Check duplicate email
    result = await db.execute(select(UserDB).where(UserDB.email == user.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400, detail=f"The email '{user.email}' is already registered"
        )

    db_user = UserDB(
        # id
        code=user.code,
        pin=user.pin,
        # district
        district_id=user.district_id,
        # personal details
        fname=user.fname,
        lname=user.lname,
        position=user.position,
        # contact, address
        email=user.email,
        mobile_code=user.mobile_code,
        mobile=user.mobile,
        address_physical=user.address_physical,
        address_postal=user.address_postal,
        # account
        role_id=user.role_id,
        password=assist.hash_password(user.password),
        # walkr routes
        walk_routes=user.walk_routes,
        # approval
        status_id=user.status_id,
        stage_id=user.stage_id,
        approval_levels=user.approval_levels,
        # service
        created_by=user.created_by,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create user: f{e}")
    return db_user


@router.post("/import")
async def import_users(
    customerImport: ParamCustomerImport,
    db: AsyncSession = Depends(get_lwsc_db),
):
    # check user importing actually exists in system
    result = await db.execute(select(UserDB).where(UserDB.id == customerImport.user_id))

    userSystem = result.scalars().first()

    if not userSystem:
        # user does not exist
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{customerImport.user_id}' does not exist",
        )

    # get all existig routes
    result = await db.execute(
        select(WalkRouteDB).where(WalkRouteDB.status_id == assist.STATUS_APPROVED)
    )

    existingRoutes = result.scalars().all()

    # start processing
    index = 0
    added = 0
    updated = 0

    startProcess = assist.get_current_date(False)

    # init an empty dictionary to store who has been processed
    # dict makes it earsier to access details for each reader than list
    processedImportReaders = {}

    # loop through each item being imported. See below for file format.

    # Account	Meter	StreetName[route name,]	ConsCode[meter reader name]

    for user in customerImport.items:
        # get names and assign key for dict
        names = user["ConsCode"]
        namekey = str(names).replace(" ", "")

        # assign random email
        email = f"{uuid4().hex}@lpwsc.co.zm"

        # get the route
        routename = user["StreetName"]

        # check if name already processed
        if namekey in processedImportReaders:
            # reader processed before

            # get existing set for routes for this reader
            items = set(processedImportReaders[namekey]["routes"])

            # add current route. Will not add anything if existing since its set
            items.add(routename)

            # assign updated list of routes to reader
            processedImportReaders[namekey]["routes"] = items
        else:
            # reader not ptocessed

            # create empty dict to hold info about this reader
            processedImportReaders[namekey] = {}

            # assign names and email
            processedImportReaders[namekey]["email"] = email
            processedImportReaders[namekey]["names"] = names

            # assign new set to hold routes with current route
            processedImportReaders[namekey]["routes"] = {routename}

    # get all raeder jeys
    keys = processedImportReaders.keys()

    for key in keys:

        # for each reader, get all routes in system that match with current
        # list of routes for this reader and in current district
        # routes re added when importing customers not here

        # update count
        index += 1

        # get details
        names = processedImportReaders[key]["names"]
        email = processedImportReaders[key]["email"]
        items = processedImportReaders[key]["routes"]

        result = await db.execute(
            select(WalkRouteDB)
            .options(
                load_only(
                    WalkRouteDB.id,
                    WalkRouteDB.name,
                    WalkRouteDB.district_id,
                ),
                selectinload(WalkRouteDB.district).load_only(
                    DistrictDB.id, DistrictDB.name, DistrictDB.code
                ),
            )
            .where(
                WalkRouteDB.name.in_(items),
                WalkRouteDB.district_id == customerImport.district_id,
            )
        )

        existingRoutes = result.scalars().all()

        # create a list for this routes
        routes = [
            WalkRouteWithSimpleDetail.from_orm(obj).dict() for obj in existingRoutes
        ]

        # check if this reader exists
        result = await db.execute(
            select(UserDB)
            .options(
                selectinload(UserDB.stage),
                selectinload(UserDB.status),
                selectinload(UserDB.role),
            )
            .where(
                UserDB.fname == names,
            )
        )

        existingUser = result.scalars().first()

        if existingUser:
            # exists, update user available fields
            existingUser.fname = names
            existingUser.walk_routes = routes
            existingUser.district_id = customerImport.district_id
            # commit
            try:
                await db.commit()
                await db.refresh(existingUser)

                updated += 1
            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Unable to update meter reader {e}"
                )

            # keep track of the reader we just processed
            readerUser = existingUser
        else:
            # doesnt exist, add user

            db_user = UserDB(
                # id
                code=None,
                pin=email[:5],
                # district
                district_id=customerImport.district_id,
                # personal details
                fname=names,
                lname="--",
                position="Meter Reader",
                # contact, address
                email=email,
                mobile_code="+260",
                mobile="977123456",
                address_physical=None,
                address_postal=None,
                # account
                role_id=lwscapp.ROLE_METERREADER,
                password=assist.hash_password(email[:5]),
                # walkr routes
                walk_routes=routes,
                # approval
                status_id=lwscapp.STATUS_APPROVED,
                stage_id=lwscapp.APPROVAL_STAGE_APPROVED,
                approval_levels=1,
                # service
                created_by=userSystem.email,
            )
            db.add(db_user)
            added += 1

            # commit changes
            try:
                # comit changes
                await db.commit()
                await db.refresh(db_user)

                # update code
                db_user.code = f"MR{str(db_user.id).zfill(5)}"
                db_user.pin = email[:5]

                await db.commit()

            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Unable to import neter readers: f{e}"
                )

            # keep track of the reader we just processed
            readerUser = db_user

        # capture the walk routes for this reader in the reader routes table

        # remove the routes currently assigned to this reader first
        await db.execute(
            delete(MeterReaderWalkRouteDB).where(
                MeterReaderWalkRouteDB.user_id == readerUser.id
            )
        )

        # add the routes found for this reader. Use a set of ids so a route
        # is not assigned twice when the same route name is repeated
        for route_id in {obj.id for obj in existingRoutes}:
            db.add(
                MeterReaderWalkRouteDB(
                    # user
                    user_id=readerUser.id,
                    # route
                    route_id=route_id,
                    # service
                    created_by=userSystem.email,
                )
            )

        # commit changes
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Unable to import meter reader walk routes: f{e}",
            )

    endProcess = assist.get_current_date(False)

    print(f"Import Duration. Start={startProcess}, End={endProcess}")

    return {
        "succeeded": True,
        "message": f"Successfully imported {index} meter reader(s). Updated {updated} and added {added} customer(s)",
    }


@router.put("/update/{user_id}", response_model=UserWithDetail)
async def update_configuration(
    user_id: int, config_update: User, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(
        select(UserDB)
        .options(
            selectinload(UserDB.stage),
            selectinload(UserDB.status),
            selectinload(UserDB.role),
        )
        .where(UserDB.id == user_id)
        .order_by(UserDB.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404, detail=f"Unable to find user with id '{user_id}'"
        )

    # Update fields that are not None
    for key, value in config_update.dict(exclude_unset=True).items():
        # if password, encrypt
        if key == "password":
            setattr(user, key, assist.hash_password(value))
        else:
            setattr(user, key, value)

    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update user {e}")
    return user


@router.get("/id/{user_id}", response_model=ParamUserEdit)
async def get_user_id(user_id: int, db: AsyncSession = Depends(get_lwsc_db)):

    userItem = None
    if user_id != 0:
        result = await db.execute(
            select(UserDB)
            .options(
                selectinload(UserDB.stage),
                selectinload(UserDB.status),
                selectinload(UserDB.role),
            )
            .where(UserDB.id == user_id)
            .order_by(UserDB.email)
        )

        userItem = result.scalars().first()
        if not userItem:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to find user with specified id '{user_id}'",
            )
    # towns
    result = await db.execute(select(DistrictDB))
    districtList = result.scalars().all()

    # walk routes
    result = await db.execute(
        select(WalkRouteDB).options(
            selectinload(WalkRouteDB.district),
        )
    )

    routeList = result.scalars().all()

    param = ParamUserEdit(user=userItem, districts=districtList, routes=routeList)

    return param


@router.get("/email/{user_email}", response_model=List[UserSimple])
async def get_user_email(user_email: str, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(UserDB).where(UserDB.email == user_email))
    users = []

    user = result.scalars().first()
    if user:
        users.append(user)

    return users


@router.get("/list", response_model=List[UserWithDetail])
async def list_users(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(UserDB)
        .options(
            selectinload(UserDB.stage),
            selectinload(UserDB.status),
            selectinload(UserDB.role),
        )
        .order_by(UserDB.email)
    )
    return result.scalars().all()


@router.get("/meter-reader/list", response_model=List[UserWithDetail])
async def list_meter_reader_users(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(UserDB)
        .options(
            selectinload(UserDB.stage),
            selectinload(UserDB.status),
            selectinload(UserDB.role),
        )
        .where(UserDB.role_id == lwscapp.ROLE_METERREADER)
        .order_by(UserDB.email)
    )
    return result.scalars().all()


@router.get(
    "/walk-routes/{user_id}", response_model=List[MeterReaderWalkRouteWithDetail]
)
async def list_user_walk_routes(
    user_id: int, db: AsyncSession = Depends(get_lwsc_db)
):
    # check the user exists
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))

    existingUser = result.scalars().first()

    if not existingUser:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{user_id}' does not exist"
        )

    # get all routes assigned to this user
    result = await db.execute(
        select(MeterReaderWalkRouteDB)
        .options(
            selectinload(MeterReaderWalkRouteDB.user),
            selectinload(MeterReaderWalkRouteDB.route).selectinload(
                WalkRouteDB.district
            ),
        )
        .where(MeterReaderWalkRouteDB.user_id == user_id)
    )

    return result.scalars().all()


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    adminList = validation.get_validation_users()

    index = 1

    for value in adminList:
        db_status = UserDB(
            # id
            code=f"UM00{index}",
            # personal details
            fname=value["fname"],
            lname=value["lname"],
            position=value["position"],
            # contact, address
            email=value["email"],
            mobile=value["mobile"],
            mobile_code="+260",
            address_physical=value["address_physical"],
            address_postal=value["address_postal"],
            # account
            role_id=value["role"],
            password=assist.hash_password(value["password"]),
            # approval
            status_id=value["status_id"],
            stage_id=value["stage_id"],
            approval_levels=value["approval_levels"],
            # service
            created_by=value["created_by"],
        )
        db.add(db_status)
        index += 1

    try:
        await db.commit()
        # await db.refresh(db_status)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to initialize users: f{e}")
    return {
        "succeeded": True,
        "message": "Users have been successfully initialized",
    }


@router.put("/review-update/{id}", response_model=UserWithDetail)
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
    result = await db.execute(select(UserDB).where(UserDB.id == id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find user with id '{id}' not found",
        )

    if user.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{id}' has already been approved",
        )

    user.updated_by = user.email

    approveUser = False

    if user.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        if user.created_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the primary reviewer of an user you created",
            )

        user.review1_at = assist.get_current_date(False)
        user.review1_by = user.email
        user.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            user.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if user.approval_levels == 1:
                # one level, no furthur stage approvers

                # approve user
                approveUser = True

            elif user.approval_levels == 2 or user.approval_levels == 3:
                # two or three levels, move to primary

                user.stage_id = assist.APPROVAL_STAGE_PRIMARY

    elif user.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage

        if user.review1_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the secondary reviewer since you were the primary reviewer",
            )

        user.review2_at = assist.get_current_date(False)
        user.review2_by = user.email
        user.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            user.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if user.approval_levels == 2:
                # two levels, no furthur stage approvers

                approveUser = True

            elif user.approval_levels == 3:
                # three levels, move to secondary
                user.stage_id = assist.APPROVAL_STAGE_SECONDARY

    elif user.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage

        if user.review2_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the final reviewer since you were the secondary reviewer",
            )

        user.review3_at = assist.get_current_date(False)
        user.review3_by = user.email
        user.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            user.status_id = assist.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage
            approveUser = True

    if approveUser:
        # change user status
        user.status_id = assist.STATUS_APPROVED
        user.stage_id = assist.APPROVAL_STAGE_APPROVED

        # attachment may or may not be provided

    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update user: {e}")
    return user
