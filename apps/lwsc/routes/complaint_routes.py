from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Any
from sqlalchemy.orm import selectinload
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.customer_category_model import CategoryDB
from apps.lwsc.models.complaint_model import Complaint, ComplaintDB, ComplaintWithDetail
from apps.lwsc.models.customer_model import CustomerDB
from apps.lwsc.models.district_model import DistrictDB
from apps.lwsc.models.user_model import UserDB
from apps.lwsc.models.walkroute_model import WalkRouteDB
from helpers import assist
import random
from apps.lwsc import lwscapp
from sqlalchemy.orm import noload

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("/create/{customer_no}", response_model=Complaint)
async def create_type(customer_no: str, complaint: Complaint, db: AsyncSession = Depends(get_lwsc_db)):
    # get customer
    result = await db.execute(
        select(CustomerDB).options(noload("*")).where(CustomerDB.account == customer_no)
    )
    customerItem = result.scalars().first()
    if not customerItem:
        raise HTTPException(
            status_code=404, detail=f"Unable to find customer with account '{customer_no}'"
        )

    db_user = ComplaintDB(
        #uuid
        uuid=complaint.uuid,
        # customer
        customer_id=customerItem.id,
        # department
        department_id=complaint.department_id,
        # complaint
        reference_number=complaint.reference_number,
        category=complaint.category,
        priority=complaint.priority,
        description=complaint.description,
        preferred_contact_method=complaint.preferred_contact_method,
        is_emergency=complaint.is_emergency,
        # approval
        status_id=complaint.status_id,
        stage_id=complaint.stage_id,
        approval_levels=complaint.approval_levels,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create complaint: f{e}")
    return db_user




@router.get("/id/{complaint_id}", response_model=ComplaintWithDetail)
async def get_complaint(complaint_id: int, db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(ComplaintDB)
        .options(
            selectinload(ComplaintDB.customer),
            selectinload(ComplaintDB.department),
            selectinload(ComplaintDB.stage),
            selectinload(ComplaintDB.status),
        )
        .where(ComplaintDB.id == complaint_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=404, detail=f"Unable to find complaint with id '{complaint_id}'"
        )
    return category




@router.put("/update/{complaint_id}", response_model=ComplaintWithDetail)
async def update_category(
    complaint_id: int, complaint_update: Complaint, db: AsyncSession = Depends(get_lwsc_db)
):
    result = await db.execute(
        select(ComplaintDB)
        .options(
            selectinload(ComplaintDB.customer),
            selectinload(ComplaintDB.department),
            selectinload(ComplaintDB.stage),
            selectinload(ComplaintDB.status),
        )
        .where(ComplaintDB.id == complaint_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"Unable to find complaint with id '{complaint_id}'"
        )

    # Update fields that are not None
    for key, value in complaint_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update complaint {e}")
    return config


@router.get("/list", response_model=List[ComplaintWithDetail])
async def list_complaints(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(
        select(ComplaintDB)
        .options(
            selectinload(ComplaintDB.customer),
            selectinload(ComplaintDB.department),
            selectinload(ComplaintDB.stage),
            selectinload(ComplaintDB.status),
        )
        .order_by(ComplaintDB.created_at)
    )
    return result.scalars().all()

