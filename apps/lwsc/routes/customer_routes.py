from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.customer_model import (
    Customer,
    CustomerDB,
    CustomerSimple,
    CustomerWithDetail,
)
from apps.lwsc.models.user_model import UserDB
from apps.lwsc.models.walkroute_model import WalkRouteDB
from helpers import assist
import random
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


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    # get all routes
    result = await db.execute(select(WalkRouteDB))
    routes = result.scalars().all()

    #add 3 customers for each 
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
                fname=f'T{route.town_id} R{route.id} Customer {k}',
                lname=f'T{route.town_id} R{route.id} Name {k}',
                title='Mr.',
                # contact, address
                email=f't{route.town_id}.r{route.id}.customer{k}@yahoo.com',
                mobile=f'260955123{pad}',
                tel=f'260955123{pad}',
                address_physical=f"Plot 397{pad}. Off Samfya Road",
                address_postal=f"P.O Box 790{pad}",
                lat=-11.1818469 - (index * 100),
                lon=28.8866439 + (index * 100),
                # approval
                status_id=assist.STATUS_APPROVED,
                stage_id=assist.APPROVAL_STAGE_APPROVED,
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
async def get_knowledgebase_category(
    customer_id: int, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(select(CustomerDB).filter(CustomerDB.id == customer_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404, detail=f"Unable to find customer with id '{customer_id}'"
        )
    return category


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
    result = await db.execute(select(CustomerDB))
    return result.scalars().all()


@router.get("/items", response_model=List[CustomerSimple])
async def list_customers(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(CustomerDB))
    return result.scalars().all()
