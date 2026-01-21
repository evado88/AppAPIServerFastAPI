from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from helpers import assist
from models.member_query_model import MemberQuery, MemberQueryDB, MemberQueryWithDetail
from models.review_model import SACCOReview
from models.user_model import UserDB

router = APIRouter(prefix="/member-queries", tags=["MemberQuerys"])


@router.post("/create", response_model=MemberQuery)
async def post_memberquery(mquery: MemberQuery, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == mquery.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id {mquery.user_id} does not exist"
        )

    db_tran = MemberQueryDB(
        # id
        type_id=mquery.type_id,
        # user
        user_id=mquery.user_id,
        # transaction
        title=mquery.title,
        content=mquery.content,
        # attachment
        attachment_id=mquery.attachment_id,
        # approval
        status_id=mquery.status_id,
        stage_id=mquery.stage_id,
        approval_levels=mquery.approval_levels,
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
            status_code=400, detail=f"Unable to create member query: {e}"
        )
    return db_tran


@router.get("/list", response_model=List[MemberQueryWithDetail])
async def list_memberquerys(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MemberQueryDB)
        # .options(
        #    joinedload(MemberQueryDB.post),
        #    joinedload(MemberQueryDB.status),
        #    joinedload(MemberQueryDB.type),
        #    joinedload(MemberQueryDB.source),
        #
        # )
    )
    queries = result.scalars().all()
    return queries


@router.get("/id/{memberquery_id}", response_model=MemberQueryWithDetail)
async def get_memberquery(memberquery_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MemberQueryDB)
        # .options(
        #    joinedload(MemberQueryDB.post),
        #    joinedload(MemberQueryDB.status),
        #    joinedload(MemberQueryDB.type),
        #    joinedload(MemberQueryDB.source),
        #
        # )
        .filter(MemberQueryDB.id == memberquery_id)
    )
    query = result.scalars().first()
    if not query:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find member query with id '{memberquery_id}'",
        )
    return query


@router.put("/update/{query_id}", response_model=MemberQueryWithDetail)
async def update_item(
    query_id: int, config_update: MemberQuery, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MemberQueryDB).where(MemberQueryDB.id == query_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"Unable to find member query with id '{query_id}'"
        )

    # Update fields that are not None
    for key, value in config_update.dict(exclude_unset=True).items():
        setattr(config, key, value)

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Unable to update member query {e}"
        )
    return config


@router.get("/user/{user_id}", response_model=List[MemberQueryWithDetail])
async def list_user_memberquery(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MemberQueryDB)
        # .options(
        #    joinedload(MemberQueryDB.post),
        #    joinedload(MemberQueryDB.status),
        #    joinedload(MemberQueryDB.type),
        #    joinedload(MemberQueryDB.source),
        #
        # )
        .filter(MemberQueryDB.user_id == user_id)
    )
    queries = result.scalars().all()
    return queries


@router.put("/review-update/{id}", response_model=MemberQueryWithDetail)
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
    result = await db.execute(select(MemberQueryDB).where(MemberQueryDB.id == id))
    query = result.scalar_one_or_none()

    if not query:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find query with id '{id}' not found",
        )

    if query.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The query with id '{id}' has already been approved",
        )

    query.updated_by = user.email

    approveMeeting = False

    if query.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage
        
        if query.created_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the primary reviewer of an query you created",
        )

        query.response = review.content
        query.review1_at = assist.get_current_date(False)
        query.review1_by = user.email
        query.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            query.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if query.approval_levels == 1:
                # one level, no furthur stage approvers

                # approve query
                approveMeeting = True

            elif query.approval_levels == 2 or query.approval_levels == 3:
                # two or three levels, move to primary

                query.stage_id = assist.APPROVAL_STAGE_PRIMARY

    elif query.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage
        
        if query.review1_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the secondary reviewer since you were the primary reviewer",
        )

        query.review2_at = assist.get_current_date(False)
        query.review2_by = user.email
        query.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            query.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if query.approval_levels == 2:
                # two levels, no furthur stage approvers

                approveMeeting = True

            elif query.approval_levels == 3:
                # three levels, move to secondary
                query.stage_id = assist.APPROVAL_STAGE_SECONDARY

    elif query.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage
        
        if query.review2_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the final reviewer since you were the secondary reviewer",
        )

        query.review3_at = assist.get_current_date(False)
        query.review3_by = user.email
        query.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            query.status_id = assist.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage
            approveMeeting = True

    if approveMeeting:
        # change query status
        query.status_id = assist.STATUS_APPROVED
        query.stage_id = assist.APPROVAL_STAGE_APPROVED

        # attachment may or may not be provided

    try:
        await db.commit()
        await db.refresh(query)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update query: {e}")
    return query
