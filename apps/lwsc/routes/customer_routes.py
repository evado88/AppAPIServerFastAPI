from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Any
from sqlalchemy.orm import selectinload
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.category_model import CategoryDB
from apps.lwsc.models.customer_model import (
    Customer,
    CustomerDB,
    CustomerItem,
    CustomerWithDetail,
)
from apps.lwsc.models.district_model import DistrictDB
from apps.lwsc.models.param_models import ParamCustomer, ParamCustomerImport
from apps.lwsc.models.user_model import UserDB
from apps.lwsc.models.walkroute_model import WalkRouteDB
from helpers import assist
import random
from apps.lwsc import lwscapp
from sqlalchemy.orm import noload

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/create", response_model=CustomerWithDetail)
async def create_type(customer: Customer, db: AsyncSession = Depends(get_lwsc_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == customer.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{customer.user_id}' does not exist",
        )

    db_user = CustomerDB(
        # user
        user_id=customer.user_id,
        # cat
        cat_id=customer.cat_id,
        # town
        town_id=customer.town_id,
        # route
        route_id=customer.route_id,
        # details
        name=customer.name,
        # contact, address
        email=customer.email,
        mobile=customer.mobile,
        tel=customer.tel,
        address_physical=customer.address_physical,
        address_postal=customer.address_postal,
        lat=customer.lat,
        lon=customer.lon,
        # approval
        status_id=customer.status_id,
        stage_id=customer.stage_id,
        approval_levels=customer.approval_levels,
        # service
        created_by=user.email,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create customer: f{e}")
    return db_user


@router.post("/import")
async def import_customers(
    customerImport: ParamCustomerImport,
    db: AsyncSession = Depends(get_lwsc_db),
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == customerImport.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{customerImport.user_id}' does not exist",
        )

    # existig customers
    result = await db.execute(
        select(CustomerDB).where(CustomerDB.status_id == assist.STATUS_APPROVED)
    )

    existingCustomers = result.scalars().all()

    index = 0
    added = 0
    updated = 0

    startProcess = assist.get_current_date(False)

    for customer in customerImport.items:

        # update count
        index += 1

        # get account number
        account = customer["Account"]

        # get route name
        routename = customer["StreetName"]

        # keep track if customers who exist
        customerExists = False
        customerRecord = None

        for c in existingCustomers:
            if c.account == account:
                customerExists = True
                customerRecord = c
                break

        # add route
        # check route
        result = await db.execute(
            select(WalkRouteDB)
            .options(
                selectinload(WalkRouteDB.user),
                selectinload(WalkRouteDB.district),
                selectinload(WalkRouteDB.stage),
                selectinload(WalkRouteDB.status),
            )
            .where(
                WalkRouteDB.name == routename,
                WalkRouteDB.district_id == customerImport.district_id,
            )
        )

        route = result.scalars().first()
        routeId = None

        if route:
            # route exists
            routeId = route.id
        else:
            # route doesnt exist
            db_route = WalkRouteDB(
                # user
                user_id=customerImport.user_id,
                # district
                district_id=customerImport.district_id,
                # details
                name=routename,
                # approval
                status_id=lwscapp.STATUS_APPROVED,
                stage_id=lwscapp.APPROVAL_STAGE_APPROVED,
                approval_levels=2,
            )
            db.add(db_route)
            try:
                await db.commit()
                await db.refresh(db_route)
                # get the id
                routeId = db_route.id
            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Unable to create route: f{e}"
                )

        if customerExists:
            # update customer available fields

            customerRecord.name = customer["Name"]
            customerRecord.number = customer["Meter"]
            customerRecord.address_physical = customer["StreetName"]
            customerRecord.lat = customer["Latitude"]
            customerRecord.lon = customer["Longitude"]
            customerRecord.route_id = routeId
            customerRecord.current = customer["Current"]
            customerRecord.previous = customer["Previous"]

            # commit
            try:
                await db.commit()
                await db.refresh(customerRecord)

                updated += 1
            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Unable to update customer {e}"
                )
        else:
            # add customer
            db_customer = CustomerDB(
                # user
                user_id=customerImport.user_id,
                # cat
                cat_id=customerImport.cat_id,
                # town
                district_id=customerImport.district_id,
                # route
                route_id=routeId,
                # details
                account=account,
                name=customer["Name"],
                number=customer["Meter"],
                remarks=customer["Remarks"],
                # contact, address
                email=f"{account}@lpwsc.co.zm",
                mobile="097",
                tel="",
                address_physical=customer["StreetName"],
                address_postal="",
                lat=customer["Latitude"],
                lon=customer["Longitude"],
                # reading
                current=customer["Current"],
                previous=customer["Previous"],
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
        raise HTTPException(status_code=400, detail=f"Unable to import customers: f{e}")

    endProcess = assist.get_current_date(False)

    print(f"Import Duration. Start={startProcess}, End={endProcess}")

    return {
        "succeeded": True,
        "message": f"Successfully imported {index} customer(s). Updated {updated} and added {added} customer(s)",
    }


@router.get("/id/{customer_id}", response_model=CustomerWithDetail)
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(CustomerDB)
        .options(
            selectinload(CustomerDB.user),
            selectinload(CustomerDB.category),
            selectinload(CustomerDB.district),
            selectinload(CustomerDB.route),
            selectinload(CustomerDB.stage),
            selectinload(CustomerDB.status),
        )
        .where(CustomerDB.id == customer_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404, detail=f"Unable to find customer with id '{customer_id}'"
        )
    return category


@router.get("/edit/{customer_id}", response_model=ParamCustomer)
async def get_edit_customer(customer_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    # get customer
    result = await db.execute(
        select(CustomerDB).options(noload("*")).where(CustomerDB.id == customer_id)
    )
    customerItem = result.scalars().first()
    if not customerItem:
        raise HTTPException(
            status_code=404, detail=f"Unable to find customer with id '{customer_id}'"
        )

    # district
    result = await db.execute(select(DistrictDB).options(noload("*")))
    districtList = result.scalars().all()

    # wak routes
    result = await db.execute(select(WalkRouteDB).options(noload("*")))
    routeList = result.scalars().all()

    # categories
    result = await db.execute(select(CategoryDB).options(noload("*")))
    categoryList = result.scalars().all()

    # create param
    param = ParamCustomer(
        customer=customerItem,
        districts=districtList,
        routes=routeList,
        categories=categoryList,
    )

    return param


@router.put("/update/{customer_id}", response_model=CustomerWithDetail)
async def update_category(
    customer_id: int, customer_update: Customer, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(
        select(CustomerDB)
        .options(
            selectinload(CustomerDB.user),
            selectinload(CustomerDB.category),
            selectinload(CustomerDB.district),
            selectinload(CustomerDB.route),
            selectinload(CustomerDB.stage),
            selectinload(CustomerDB.status),
        )
        .where(CustomerDB.id == customer_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"Unable to find customer with id '{customer_id}'"
        )

    # Update fields that are not None
    for key, value in customer_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update customer {e}")
    return config


@router.get("/list", response_model=List[CustomerWithDetail])
async def list_customers(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(CustomerDB)
        .options(
            selectinload(CustomerDB.user),
            selectinload(CustomerDB.category),
            selectinload(CustomerDB.district),
            selectinload(CustomerDB.route),
            selectinload(CustomerDB.stage),
            selectinload(CustomerDB.status),
        )
        .order_by(CustomerDB.account)
    )
    return result.scalars().all()


@router.get("/items", response_model=List[CustomerItem])
async def list_customers(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(CustomerDB).options(noload("*")))
    return result.scalars().all()
