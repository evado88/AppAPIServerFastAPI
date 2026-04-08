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
from apps.lwsc.models.meter_model import MeterDB
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
        # personal details
        fname=customer.fname,
        lname=customer.lname,
        title=customer.title,
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
    for customer in customerImport.items:

        # update count
        index += 1
        account = customer["Account"]

        for c in existingCustomers:
            if c.code == account:
                raise HTTPException(
                    status_code=400,
                    detail=f"The customer '{account}' already exists in the system",
                )

        # split name if it has space
        name = str(customer["Name"])

        if " " in name:
            names = name.split(" ", 1)

            firstname = names[0]
            lastname = names[1]
        else:
            firstname = name
            lastname = ""

        db_customer = CustomerDB(
            # user
            user_id=customerImport.user_id,
            # cat
            cat_id=customerImport.cat_id,
            # town
            district_id=customerImport.district_id,
            # route
            route_id=customerImport.route_id,
            # personal details
            code=account,
            fname=firstname,
            lname=lastname,
            title="",
            # contact, address
            email=f"{account}@lpwsc.co.zm",
            mobile="097",
            tel="",
            address_physical=customer["StreetName"],
            address_postal="",
            lat=customer["Latitude"],
            lon=customer["Longitude"],
            # approval
            status_id=lwscapp.STATUS_APPROVED,
            stage_id=lwscapp.APPROVAL_STAGE_APPROVED,
            approval_levels=1,
            # service
            created_by=user.email,
        )
        db.add(db_customer)
        try:
            await db.commit()
            await db.refresh(db_customer)

            db_meter = MeterDB(
                # user
                user_id=customerImport.user_id,
                # town
                district_id=customerImport.district_id,
                # customer
                customer_id=db_customer.id,
                # route
                route_id=customerImport.route_id,
                # details
                code=account,
                number=account,
                name=account,
                description="",
                # reading
                read_date=None,
                current=customer["Current"],
                previous=customer["Previous"],
                comments=None,
                # contact, address
                lat=customer["Latitude"],
                lon=customer["Longitude"],
                # approval
                status_id=lwscapp.STATUS_APPROVED,
                stage_id=lwscapp.APPROVAL_STAGE_APPROVED,
                approval_levels=1,
                # service
                created_by=user.email,
            )

            db.add(db_meter)
            await db.commit()

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400, detail=f"Unable to import customers: f{e}"
            )
    return {
        "succeeded": True,
        "message": f"Successfully imported {index} customer(s)",
    }


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    # get all routes
    result = await db.execute(select(WalkRouteDB))
    routes = result.scalars().all()

    # add 3 customers for each
    index = 1
    for route in routes:
        for k in range(1, 4):
            pad = str(index).zfill(3)
            db_status = CustomerDB(
                # user
                user_id=route.user_id,
                # cat
                cat_id=random.randint(1, 13),
                # town
                town_id=route.town_id,
                # route
                route_id=route.id,
                # personal details
                fname=f"T{route.town_id} R{route.id} Customer {k}",
                lname=f"T{route.town_id} R{route.id} Name {k}",
                title="Mr.",
                # contact, address
                email=f"t{route.town_id}.r{route.id}.customer{k}@yahoo.com",
                mobile=f"260955123{pad}",
                tel=f"260955123{pad}",
                address_physical=f"Plot 397{pad}. Off Samfya Road",
                address_postal=f"P.O Box 790{pad}",
                lat=-11.1818469 - (index * 100),
                lon=28.8866439 + (index * 100),
                # approval
                status_id=assist.STATUS_APPROVED,
                stage_id=lwscapp.APPROVAL_STAGE_APPROVED,
                approval_levels=2,
                # service
                created_by="user-001@hotmail.com",
            )
            db.add(db_status)
            index += 1

    try:
        await db.commit()
        # await db.refresh(db_status)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to initialize customers: f{e}"
        )
    return {
        "succeeded": True,
        "message": "Customers have been successfully initialized",
    }


@router.get("/id/{customer_id}", response_model=CustomerWithDetail)
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(CustomerDB).filter(CustomerDB.id == customer_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404, detail=f"Unable to find customer with id '{customer_id}'"
        )
    return category


@router.get("/edit/{customer_id}", response_model=ParamCustomer)
async def get_edit_customer(customer_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    # get customer
    result = await db.execute(select(CustomerDB).options(noload("*")).filter(CustomerDB.id == customer_id))
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
    result = await db.execute(select(CustomerDB).where(CustomerDB.id == customer_id))
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
    result = await db.execute(select(CustomerDB).options(
            selectinload(CustomerDB.user),
            selectinload(CustomerDB.category),
            selectinload(CustomerDB.district),
            selectinload(CustomerDB.route),
            selectinload(CustomerDB.stage),
            selectinload(CustomerDB.status),
        ).order_by(CustomerDB.code))
    return result.scalars().all()


@router.get("/items", response_model=List[CustomerItem])
async def list_customers(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(CustomerDB).options(noload("*")))
    return result.scalars().all()
