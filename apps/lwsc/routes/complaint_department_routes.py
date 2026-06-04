from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List

from apps.lwsc import lwscapp
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.bill_rate_model import BillRateDB
from apps.lwsc.models.complaint_department_model import (
    ComplaintDepartment,
    ComplaintDepartmentDB,
    ComplaintDepartmentItem,
    ComplaintDepartmentWithDetail,
)
from apps.lwsc.models.user_model import UserDB
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/complaint-departments", tags=["ComplaintDepartments"])


@router.post("/create", response_model=ComplaintDepartment)
async def post__category(
    category: ComplaintDepartment, db: AsyncSession = Depends(get_lwsc_db)
):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == category.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{category.user_id}' does not exist",
        )

    db_tran = ComplaintDepartmentDB(
        # user
        user_id=category.user_id,
        # transaction
        dept_name=category.cat_name,
        description=category.description,
        # service
        created_by=user.email,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to create complaint department: {e}"
        )
    return db_tran


@router.put("/update/{cat_id}", response_model=ComplaintDepartmentWithDetail)
async def update_category(
    cat_id: int,
    category_update: ComplaintDepartment,
    db: AsyncSession = Depends(get_lwsc_db),
):
    result = await db.execute(
        select(ComplaintDepartmentDB)
        .options(
            selectinload(ComplaintDepartmentDB.user),
        )
        .where(ComplaintDepartmentDB.id == cat_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find complaint department with id '{cat_id}'",
        )

    # Update fields that are not None
    for key, value in category_update.dict(exclude_unset=True).items():
        setattr(category, key, value)

    try:
        await db.commit()
        await db.refresh(category)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update complaint department {e}"
        )
    return category


@router.get("/list", response_model=List[ComplaintDepartmentWithDetail])
async def list_categories(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(ComplaintDepartmentDB)
        .options(
            selectinload(ComplaintDepartmentDB.user),
        )
        .order_by(ComplaintDepartmentDB.id)
    )
    return result.scalars().all()

@router.get("/items", response_model=List[ComplaintDepartmentItem])
async def list_items(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(ComplaintDepartmentDB)
        .options(
            selectinload(ComplaintDepartmentDB.user),
        )
        .order_by(ComplaintDepartmentDB.id)
    )
    return result.scalars().all()

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    departments = [
        {
            "id": "CUSTOMER_SERVICE",
            "name": "Customer Service",
            "description": (
                "Handles general customer inquiries, complaint intake, "
                "account-related issues, customer communication, and routing "
                "complaints to the appropriate department."
            ),
        },
        {
            "id": "BILLING",
            "name": "Billing & Revenue",
            "description": (
                "Handles billing disputes, overbilling complaints, tariff queries, "
                "bill adjustments, and revenue-related investigations."
            ),
        },
        {
            "id": "METER_READING",
            "name": "Meter Reading",
            "description": (
                "Handles incorrect meter readings, estimated readings, "
                "reading verification, and meter reading discrepancies."
            ),
        },
        {
            "id": "PREPAID_SERVICES",
            "name": "Prepaid Services",
            "description": (
                "Handles token generation issues, token delivery failures, "
                "invalid token complaints, and prepaid meter support."
            ),
        },
        {
            "id": "PAYMENTS",
            "name": "Payments & Reconciliation",
            "description": (
                "Handles failed payments, duplicate payments, missing transactions, "
                "refund requests, and payment reconciliation issues."
            ),
        },
        {
            "id": "TECHNICAL_SUPPORT",
            "name": "Technical Support",
            "description": (
                "Handles application errors, login problems, account access issues, "
                "mobile and web platform technical support."
            ),
        },
        {
            "id": "METER_MAINTENANCE",
            "name": "Meter Maintenance",
            "description": (
                "Handles faulty meters, damaged meters, meter inspections, "
                "repairs, and replacement requests."
            ),
        },
        {
            "id": "NETWORK_OPERATIONS",
            "name": "Network Operations",
            "description": (
                "Handles power outages, low voltage complaints, service interruptions, "
                "network faults, and electricity supply issues."
            ),
        },
        {
            "id": "CONNECTIONS",
            "name": "Connections & Disconnections",
            "description": (
                "Handles new service connections, reconnections, disconnections, "
                "service activation requests, and related disputes."
            ),
        },
        {
            "id": "FIELD_OPERATIONS",
            "name": "Field Operations",
            "description": (
                "Handles complaints requiring physical site visits, inspections, "
                "customer premises investigations, and field-based resolutions."
            ),
        },
        {
            "id": "FRAUD_COMPLIANCE",
            "name": "Fraud & Compliance",
            "description": (
                "Handles reports of meter tampering, illegal connections, "
                "energy theft, fraud investigations, and compliance matters."
            ),
        },
        {
            "id": "GIS_ASSET_MANAGEMENT",
            "name": "GIS & Asset Management",
            "description": (
                "Handles location-related issues, asset mapping discrepancies, "
                "service point verification, and infrastructure records management."
            ),
        },
        {
            "id": "ESCALATIONS",
            "name": "Escalations",
            "description": (
                "Handles escalated complaints, unresolved cases, SLA breaches, "
                "management reviews, and high-priority customer concerns."
            ),
        },
    ]
    total = 0

    for value in departments:
        db_category = ComplaintDepartmentDB(
            # personal details
            user_id=1,
            dept_name=value["name"],
            description=value["description"],
            # service
            created_by='system',
        )
        db.add(db_category)
        total += 1

    try:
        await db.commit()
        await db.refresh(db_category)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Unable to initialize complaint department '{value}': f{e}",
        )

    return {
        "succeeded": True,
        "message": f"{total} Complaint departments have been successfully initialized",
    }


@router.get("/id/{cat_id}", response_model=ComplaintDepartmentWithDetail)
async def get_category(cat_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(ComplaintDepartmentDB)
        .options(
            selectinload(ComplaintDepartmentDB.user),
        )
        .where(ComplaintDepartmentDB.id == cat_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find complaint department with id '{cat_id}'",
        )
    return category
