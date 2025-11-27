from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from helpers import assist
from models.knowledge_base_model import (
    KnowledgeBase,
    KnowledgeBaseDB,
    KnowledgeBaseWithDetail,
)
from models.review_model import SACCOReview
from models.user_model import UserDB
from sqlalchemy import desc

router = APIRouter(prefix="/knowledge-base-articles", tags=["KnowledgeBaseArticles"])


@router.post("/create", response_model=KnowledgeBase)
async def post_kbarticle(kbarticle: KnowledgeBase, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == kbarticle.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"The user with id '{kbarticle.user_id}' does not exist",
        )

    db_tran = KnowledgeBaseDB(
        # user
        user_id=kbarticle.user_id,
        # transaction
        cat_id=kbarticle.cat_id,
        title=kbarticle.title,
        content=kbarticle.content,
        # attachment
        attachment_id=kbarticle.attachment_id,
        # approval
        status_id=kbarticle.status_id,
        stage_id=kbarticle.stage_id,
        approval_levels=kbarticle.approval_levels,
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
            status_code=400, detail=f"Unable to create knowledge base article: {e}"
        )
    return db_tran


@router.put("/update/{config_id}", response_model=KnowledgeBaseWithDetail)
async def update_configuration(
    config_id: int, config_update: KnowledgeBase, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(KnowledgeBaseDB).where(KnowledgeBaseDB.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find knowledgebase article with id '{config_id}'",
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
            status_code=400, detail=f"Unable to update knowledgebase article {e}"
        )
    return config


@router.get("/list", response_model=List[KnowledgeBaseWithDetail])
async def list_kbarticles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeBaseDB)
        # .options(
        #    joinedload(KnowledgeBaseDB.post),
        #    joinedload(KnowledgeBaseDB.status),
        #    joinedload(KnowledgeBaseDB.type),
        #    joinedload(KnowledgeBaseDB.source),
        #
        # )
    )
    kbarticles = result.scalars().all()
    return kbarticles


@router.get("/recent", response_model=List[KnowledgeBaseWithDetail])
async def list_recent_kbarticles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeBaseDB)
        .where(
            KnowledgeBaseDB.status_id == assist.STATUS_APPROVED,
        )
        .limit(3)
        .order_by(desc(KnowledgeBaseDB.id))
    )
    kbarticles = result.scalars().all()
    return kbarticles


@router.get("/id/{kbarticle_id}", response_model=KnowledgeBaseWithDetail)
async def get_kbarticle_id(kbarticle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeBaseDB)
        # .options(
        #    joinedload(KnowledgeBaseDB.post),
        #    joinedload(KnowledgeBaseDB.status),
        #    joinedload(KnowledgeBaseDB.type),
        #    joinedload(KnowledgeBaseDB.source),
        #
        # )
        .filter(KnowledgeBaseDB.id == kbarticle_id)
    )
    kbarticle = result.scalars().first()
    if not kbarticle:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find knowledge base article with id '{kbarticle_id}'",
        )
    return kbarticle


@router.put("/review-update/{id}", response_model=KnowledgeBaseWithDetail)
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
    result = await db.execute(select(KnowledgeBaseDB).where(KnowledgeBaseDB.id == id))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find article with id '{id}' not found",
        )

    if article.status_id == assist.STATUS_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"The article with id '{id}' has already been approved",
        )

    article.updated_by = user.email

    approveMeeting = False

    if article.stage_id == assist.APPROVAL_STAGE_SUBMITTED:
        # submitted stage

        if article.created_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the primary reviewer of an article you created",
            )

        article.review1_at = assist.get_current_date(False)
        article.review1_by = user.email
        article.review1_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            article.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if article.approval_levels == 1:
                # one level, no furthur stage approvers

                # approve article
                approveMeeting = True

            elif article.approval_levels == 2 or article.approval_levels == 3:
                # two or three levels, move to primary

                article.stage_id = assist.APPROVAL_STAGE_PRIMARY

    elif article.stage_id == assist.APPROVAL_STAGE_PRIMARY:
        # primary stage

        if article.review1_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the secondary reviewer since you were the primary reviewer",
            )

        article.review2_at = assist.get_current_date(False)
        article.review2_by = user.email
        article.review2_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            article.status_id = assist.STATUS_REJECTED
        else:
            # approve

            # check number of approval levels
            if article.approval_levels == 2:
                # two levels, no furthur stage approvers

                approveMeeting = True

            elif article.approval_levels == 3:
                # three levels, move to secondary
                article.stage_id = assist.APPROVAL_STAGE_SECONDARY

    elif article.stage_id == assist.APPROVAL_STAGE_SECONDARY:
        # secondary stage

        if article.review2_by == user.email:
            raise HTTPException(
                status_code=400,
                detail=f"You cannot be the final reviewer since you were the secondary reviewer",
            )

        article.review3_at = assist.get_current_date(False)
        article.review3_by = user.email
        article.review3_comments = review.comments

        if review.review_action == assist.REVIEW_ACTION_REJECT:
            # reject

            article.status_id = assist.STATUS_REJECTED
        else:
            # approve
            # three levels and on last stage
            approveMeeting = True

    if approveMeeting:
        # change article status
        article.status_id = assist.STATUS_APPROVED
        article.stage_id = assist.APPROVAL_STAGE_APPROVED

        # attachment may or may not be provided

    try:
        await db.commit()
        await db.refresh(article)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update article: {e}")
    return article
