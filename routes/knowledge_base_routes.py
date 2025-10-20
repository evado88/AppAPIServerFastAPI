from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.knowledge_base_model import KnowledgeBase, KnowledgeBaseDB, KnowledgeBaseWithDetail
from models.user_model import UserDB

router = APIRouter(prefix="/knowledge-base-articles", tags=["KnowledgeBaseArticles"])


@router.post("/create", response_model=KnowledgeBase)
async def post_kbarticle(kbarticle: KnowledgeBase, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == kbarticle.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id '{kbarticle.user_id}' does not exist"
        )

    db_tran = KnowledgeBaseDB(
        # user
        user_id = kbarticle.user_id,
        # transaction
        cat_id = kbarticle.cat_id,
        title = kbarticle.title,
        content = kbarticle.content,

        # approval
        status_id = kbarticle.status_id,
        stage_id = kbarticle.stage_id,
        approval_levels = kbarticle.approval_levels,
  
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create knowledge base article: {e}")
    return db_tran

@router.put("/update/{config_id}", response_model=KnowledgeBaseWithDetail)
async def update_configuration(config_id: int, config_update: KnowledgeBase, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeBaseDB)
        .where(KnowledgeBaseDB.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Unable to find knowledgebase article with id '{config_id}'")
    
    # Update fields that are not None
    for key, value in config_update.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
        
    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update knowledgebase article {e}")
    return config


@router.get("/list", response_model=List[KnowledgeBaseWithDetail])
async def list_kbarticles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeBaseDB)
        #.options(
        #    joinedload(KnowledgeBaseDB.post),
        #    joinedload(KnowledgeBaseDB.status),
        #    joinedload(KnowledgeBaseDB.type),
        #    joinedload(KnowledgeBaseDB.source),
        #
        #)
    )
    kbarticles = result.scalars().all()
    return kbarticles


@router.get("/id/{kbarticle_id}", response_model=KnowledgeBaseWithDetail)
async def get_kbarticle_id(kbarticle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeBaseDB)
        #.options(
        #    joinedload(KnowledgeBaseDB.post),
        #    joinedload(KnowledgeBaseDB.status),
        #    joinedload(KnowledgeBaseDB.type),
        #    joinedload(KnowledgeBaseDB.source),
        #
        #)
        .filter(KnowledgeBaseDB.id == kbarticle_id)
    )
    kbarticle = result.scalars().first()
    if not kbarticle:
        raise HTTPException(status_code=404, detail=f"Unable to find knowledge base article with id '{kbarticle_id}'")
    return kbarticle
