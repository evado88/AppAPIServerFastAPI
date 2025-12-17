from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from helpers import assist, validation
from models.attachment_model import AttachmentDB
from models.member_model import Member, MemberDB, MemberWithDetail
from models.review_model import SACCOReview
from models.user_model import User, UserDB

router = APIRouter(prefix="/members", tags=["Members"])


@router.post("/register", response_model=Member)
async def register_member(member: Member, db: AsyncSession = Depends(get_db)):
    # Check duplicate email
    result = await db.execute(select(UserDB).where(UserDB.email == member.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = MemberDB(
        # id
        number=member.number,
        user_id=member.user_id,
        # personal details
        fname=member.fname,
        lname=member.lname,
        dob=member.dob,
        position=member.position,
        # id
        id_type=member.id_type,
        id_no=member.id_no,
        id_attachment=member.id_attachment,
        # contact, address
        email=member.email,
        mobile1=member.mobile1,
        mobile2=member.mobile2,
        address_physical=member.address_physical,
        address_postal=member.address_postal,
        # guarantor
        guar_fname=member.guar_fname,
        guar_lname=member.guar_lname,
        guar_mobile=member.guar_mobile,
        guar_email=member.guar_email,
        # banking
        bank_name=member.bank_name,
        bank_branch_name=member.bank_branch_name,
        bank_branch_code=member.bank_branch_code,
        bank_account_name=member.bank_account_name,
        bank_account_no=member.bank_account_no,
        # account
        password=assist.hash_password(member.password),
        # approval
        status_id=member.status_id,
        stage_id=member.stage_id,
        approval_levels=member.approval_levels,
        # service
        created_by=member.email,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to register member: f{e}")
    return db_user


@router.put("/update/{id}", response_model=MemberWithDetail)
async def update_member(
    id: int, member_update: Member, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MemberDB).where(MemberDB.id == id))
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find member with id '{id}'",
        )

    # Update fields that are not None
    for key, value in member_update.dict(exclude_unset=True).items():
        setattr(member, key, value)

    try:
        await db.commit()
        await db.refresh(member)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update member {e}")
    return member


@router.get("/id/{member_id}", response_model=MemberWithDetail)
async def get_member(member_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MemberDB)
        # .options(
        #    joinedload(TransactionDB.post),
        #    joinedload(TransactionDB.status),
        #    joinedload(TransactionDB.type),
        #    joinedload(TransactionDB.source),
        #
        # )
        .filter(MemberDB.id == member_id)
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(
            status_code=404, detail=f"Member with id '{member_id}' not found"
        )
    return transaction


@router.get("/list", response_model=List[MemberWithDetail])
async def list_members(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MemberDB))
    return result.scalars().all()


@router.get("/status/{status_id}", response_model=List[MemberWithDetail])
async def list_members(status_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MemberDB).filter(MemberDB.status_id == status_id))
    return result.scalars().all()


@router.put("/review-update/{id}", response_model=MemberWithDetail)
async def review_posting(
    id: int, review: SACCOReview, db: AsyncSession = Depends(get_db)
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
    result = await db.execute(select(MemberDB).where(MemberDB.id == id))
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find member with id '{id}' not found",
        )

    if member.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The member with id '{id}' has already been approved",
        )

    member.updated_by = user.email

    approveMember = False

    if member.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        if member.created_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the primary reviewer of a member you created",
            )

        member.review1_at = assist.get_current_date(False)
        member.review1_by = user.email
        member.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            member.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if member.approval_levels == 1:
                # one level, no furthur stage approvers

                # approve member
                approveMember = True

            elif member.approval_levels == 2 or member.approval_levels == 3:
                # two or three levels, move to primary

                member.stage_id = assist.APPROVAL_STAGE_PRIMARY

    elif member.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage

        if member.review1_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the secondary reviewer since you were the primary reviewer",
            )

        member.review2_at = assist.get_current_date(False)
        member.review2_by = user.email
        member.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            member.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if member.approval_levels == 2:
                # two levels, no furthur stage approvers

                approveMember = True

            elif member.approval_levels == 3:
                # three levels, move to secondary
                member.stage_id = assist.APPROVAL_STAGE_SECONDARY

    elif member.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage

        if member.review2_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the final reviewer since you were the secondary reviewer",
            )

        member.review3_at = assist.get_current_date(False)
        member.review3_by = user.email
        member.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            member.status_id = assist.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage
            approveMember = True

    if approveMember:
        # change member status
        member.status_id = assist.STATUS_APPROVED
        member.stage_id = assist.APPROVAL_STAGE_APPROVED

        # get attachment
        if not member.id_attachment == None:
            result = await db.execute(
                select(AttachmentDB).filter(AttachmentDB.id == member.id_attachment)
            )
            attachment = result.scalars().first()
            if not attachment:
                raise HTTPException(
                    status_code=404, detail=f"Attachment with id '{id}' not found"
                )
            
         # add corresponding user
        db_user = UserDB(
            # id
            code=f"UM00{member.id}",
            # personal details
            fname=member.fname,
            lname=member.lname,
            position=member.position,
            # contact, address
            email=member.email,
            mobile=member.mobile1,
            address_physical=member.address_physical,
            address_postal=member.address_postal,
            # account
            role=1,
            password=member.password,
            # approval
            status_id=assist.STATUS_APPROVED,
            stage_id=assist.APPROVAL_STAGE_APPROVED,
            approval_levels=member.approval_levels,
            # service
            created_by=member.email,
        )
        db.add(db_user)

    try:
        await db.commit()
        await db.refresh(member)
        
        if approveMember:
            #only do this at last stage
            await db.refresh(db_user)
            
            member.user_id = db_user.id
            
            await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to review member: {e}")
    return member

@router.post("/initialize-validation-members")
async def initialize_validation_members(db: AsyncSession = Depends(get_db)):

    members = validation.get_validation_members()
    admins = validation.get_validation_admins()

    index = 1

    for value in members:
        # add member
        username = value["email"]

        db_member = MemberDB(
            # id
            number=f"M00{index}",
            # user_id
            user_id = index,
            # personal details
            fname=value["fname"],
            lname=value["lname"],
            dob=value["dob"],
            position=value["position"],
            # id
            id_type=value["id_type"],
            id_no=value["id_no"],
            id_attachment=value["id_attachment"],
            # contact, address
            email=value["email"],
            mobile1=value["mobile1"],
            mobile2=value["mobile2"],
            address_physical=value["address_physical"],
            address_postal=value["address_postal"],
            # guarantor
            guar_fname=value["guar_fname"],
            guar_lname=value["guar_lname"],
            guar_mobile=value["guar_mobile"],
            guar_email=value["guar_email"],
            # banking
            bank_name=value["bank_name"],
            bank_branch_name=value["bank_branch_name"],
            bank_branch_code=value["bank_branch_code"],
            bank_account_name=value["bank_account_name"],
            bank_account_no=value["bank_account_no"],
            # account
            password=assist.hash_password(value["password"]),
            # approval
            status_id=value["status_id"],
            stage_id=value["stage_id"],
            approval_levels=value["approval_levels"],
            # service
            created_by=value["created_by"],
        )
    

        # add corresponding user
        db_user = UserDB(
            # id
            code=f"UM00{index}",
            # personal details
            fname=value["fname"],
            lname=value["lname"],
            position=value["position"],
            # contact, address
            email=value["email"],
            mobile=value["mobile1"],
            address_physical=value["address_physical"],
            address_postal=value["address_postal"],
            # account
            role=1,
            password=assist.hash_password("12345678"),
            # approval
            status_id=value["status_id"],
            stage_id=value["stage_id"],
            approval_levels=value["approval_levels"],
            # service
            created_by=value["created_by"],
        )
        
        db.add(db_user)
        db.add(db_member)

        try:
            await db.commit()
            index += 1
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Unable to initialize member {index} '{username}': f{e}",
            )
            
    for value in admins:
        # add  user
        username = value["email"]

        db_user = UserDB(
            # id
            code=f"UD00{index}",
            # personal details
            fname=value["fname"],
            lname=value["lname"],
            position=value["position"],
            # contact, address
            email=value["email"],
            mobile=value["mobile"],
            address_physical=value["address_physical"],
            address_postal=value["address_postal"],
            # account
            role=value["role"],
            password=assist.hash_password(value["password"]),
            # approval
            status_id=value["status_id"],
            stage_id=value["stage_id"],
            approval_levels=value["approval_levels"],
            # service
            created_by=value["created_by"],
        )
        db.add(db_user)
        index += 1

        try:
            await db.commit()
            await db.refresh(db_user)
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Unable to initialize user {index} '{username}': f{e}",
        )

    return {
        "succeeded": True,
        "message": "Validation members have been successfully initialized",
    }
