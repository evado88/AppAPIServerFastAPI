from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Any
from sqlalchemy.orm import selectinload
from apps.tpsuperapp.tpsuperappdb import get_tpsuperapp_db
from apps.tpsuperapp.models.complaint_department_model import ComplaintDepartmentDB
from apps.tpsuperapp.models.customer_category_model import CategoryDB
from apps.tpsuperapp.models.complaint_model import Complaint, ComplaintDB, ComplaintWithDetail
from apps.tpsuperapp.models.customer_model import CustomerDB
from apps.tpsuperapp.models.district_model import DistrictDB
from apps.tpsuperapp.models.param_models import ParamComplaintReview
from apps.tpsuperapp.models.review_model import AppReview
from apps.tpsuperapp.models.user_model import UserDB
from apps.tpsuperapp.models.walkroute_model import WalkRouteDB
from helpers import assist
import random
from apps.tpsuperapp import tpsuperapp
from sqlalchemy.orm import noload
from sqlalchemy import or_, desc

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("/create/{customer_no}", response_model=Complaint)
async def create_type(
    customer_no: str, complaint: Complaint, db: AsyncSession = Depends(get_tpsuperapp_db)
):
    # get customer
    result = await db.execute(
        select(CustomerDB).options(noload("*")).where(CustomerDB.account == customer_no)
    )
    customerItem = result.scalars().first()
    if not customerItem:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find customer with account '{customer_no}'",
        )

    db_user = ComplaintDB(
        # uuid
        uuid=complaint.uuid,
        # customer
        customer_id=customerItem.id,
        # complaint stage
        complaint_stage_id=complaint.complaint_stage_id,
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
async def get_complaint(complaint_id: int, db: AsyncSession = Depends(get_tpsuperapp_db)):
    result = await db.execute(
        select(ComplaintDB)
        .options(
            selectinload(ComplaintDB.customer),
            selectinload(ComplaintDB.complaintstage),
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

@router.get("/param/{complaint_id}", response_model=ParamComplaintReview)
async def get_complaint_param(complaint_id: int, db: AsyncSession = Depends(get_tpsuperapp_db)):
    result = await db.execute(
        select(ComplaintDB)
        .options(
            selectinload(ComplaintDB.customer),
            selectinload(ComplaintDB.complaintstage),
            selectinload(ComplaintDB.department),
            selectinload(ComplaintDB.stage),
            selectinload(ComplaintDB.status),
        )
        .where(ComplaintDB.id == complaint_id)
    )
    
    complaintItem = result.scalars().first()
    if not complaintItem:
        raise HTTPException(
            status_code=404, detail=f"Unable to find complaint with id '{complaint_id}'"
        )
        
    result = await db.execute(
        select(ComplaintDepartmentDB)
        .order_by(ComplaintDepartmentDB.id)
    )
    
    departmentList =  result.scalars().all()
    
    return ParamComplaintReview(complaint=complaintItem, departments=departmentList)

@router.put("/update/{complaint_id}", response_model=ComplaintWithDetail)
async def update_category(
    complaint_id: int,
    complaint_update: Complaint,
    db: AsyncSession = Depends(get_tpsuperapp_db),
):
    result = await db.execute(
        select(ComplaintDB)
        .options(
            selectinload(ComplaintDB.customer),
            selectinload(ComplaintDB.complaintstage),
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
async def list_complaints(db: AsyncSession = Depends(get_tpsuperapp_db)):
    result = await db.execute(
        select(ComplaintDB)
        .options(
            selectinload(ComplaintDB.customer),
            selectinload(ComplaintDB.complaintstage),
            selectinload(ComplaintDB.department),
            selectinload(ComplaintDB.stage),
            selectinload(ComplaintDB.status),
        )
        .order_by(ComplaintDB.created_at)
    )
    return result.scalars().all()


@router.get("/customer/{account}", response_model=List[ComplaintWithDetail])
async def list_customer_transactions(
    account: str, db: AsyncSession = Depends(get_tpsuperapp_db)
):
    result = await db.execute(
        select(CustomerDB)
        .options(
            noload("*"),
        )
        .where(CustomerDB.account == account)
    )
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(
            status_code=404, detail=f"Unable to find customer with account '{account}'"
        )

    result = await db.execute(
        select(ComplaintDB)
        .options(
            selectinload(ComplaintDB.customer),
            selectinload(ComplaintDB.complaintstage),
            selectinload(ComplaintDB.department),
            selectinload(ComplaintDB.stage),
            selectinload(ComplaintDB.status),
        )
        .where(ComplaintDB.customer_id == customer.id)
        .order_by(desc(ComplaintDB.id))
    )
    transactions = result.scalars().all()
    return transactions


@router.put("/review-update/{id}", response_model=Complaint)
async def review_posting(
    id: int, review: AppReview, db: AsyncSession = Depends(get_tpsuperapp_db)
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
    result = await db.execute(select(ComplaintDB).where(ComplaintDB.id == id))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find complaint with specified id '{id}'",
        )

    if (
        complaint.status_id == tpsuperapp.STATUS_APPROVED
        or complaint.status_id == tpsuperapp.STATUS_REJECTED
    ):
        raise HTTPException(
            status_code=400,
            detail=f"The complaint with id '{id}' has already been reviewed",
        )

    complaint.updated_by = user.email

    approveComplaint = False

    if complaint.stage_id == tpsuperapp.APPROVAL_STAGE_SUBMITTED:
        # submitted stage
        complaint.review1_at = assist.get_current_date(False)
        complaint.review1_by = user.email
        complaint.review1_comments = review.comments

        # check number of approval levels
        if complaint.approval_levels == 1:
            # one level, no furthur stage approvers

            # approve announcement
            approveComplaint = True

        elif complaint.approval_levels == 2 or complaint.approval_levels == 3:
            # two or three levels, move to primary
            # set department and assigned to
            complaint.assigned_to=review.assigned_to
            complaint.department_id = review.department_id
            complaint.stage_id = tpsuperapp.APPROVAL_STAGE_PRIMARY_REVIEW
            complaint.complaint_stage_id = tpsuperapp.COMPLAINT_STAGE_INPROGRESS
            
    elif complaint.stage_id == tpsuperapp.APPROVAL_STAGE_PRIMARY_REVIEW:
        # primary stage

        if complaint.review1_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the secondary reviewer since you were the primary reviewer",
            )

        complaint.review2_at = assist.get_current_date(False)
        complaint.review2_by = user.email
        complaint.review2_comments = review.comments
        complaint.resolution_notes = review.comments
  
        # approve

        # check number of approval levels
        if complaint.approval_levels == 2:
            # two levels, no furthur stage approvers

            approveComplaint = True

        elif complaint.approval_levels == 3:
            # three levels, move to secondary
            complaint.stage_id = tpsuperapp.APPROVAL_STAGE_SECONDARY_REVIEW

    elif complaint.stage_id == tpsuperapp.APPROVAL_STAGE_SECONDARY_REVIEW:
        # secondary stage

        if complaint.review2_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the final reviewer since you were the secondary reviewer",
            )

        complaint.review3_at = assist.get_current_date(False)
        complaint.review3_by = user.email
        complaint.review3_comments = review.comments

        # approve
        # three levels and on last stage
        approveComplaint = True

    # if rejecting or approving, resolve complaint
    if approveComplaint:
        # resolve
        complaint.status_id = tpsuperapp.STATUS_APPROVED
        complaint.stage_id = tpsuperapp.APPROVAL_STAGE_APPROVED
        complaint.complaint_stage_id = tpsuperapp.COMPLAINT_STAGE_RESOLVED
        complaint.resolved_at = assist.get_current_date(False)
    try:
        await db.commit()
        await db.refresh(complaint)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update complaint: {e}"
        )
    return complaint
