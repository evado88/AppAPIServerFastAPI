from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.knowledge_base_category_model import KnowledgeBaseCategory, KnowledgeBaseCategoryDB
from models.user_model import UserDB

router = APIRouter(prefix="/knowledge-base-categories", tags=["KnowledgeBaseCategorys"])


@router.post("/", response_model=KnowledgeBaseCategory)
async def post_knowledgebase_category(category: KnowledgeBaseCategory, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(UserDB).where(UserDB.id == category.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"The user with id {category.user_id} does not exist"
        )

    db_tran = KnowledgeBaseCategoryDB(
        # user
        user_id = category.user_id,
        # transaction
        cat_name = category.cat_name,
        description = category.description,
        # service
        created_by = category.created_by,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create knowledge base category: {e}")
    return db_tran


@router.get("/", response_model=List[KnowledgeBaseCategory])
async def list_knowledgebase_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeBaseCategoryDB)
        #.options(
        #    joinedload(KnowledgeBaseCategoryDB.post),
        #    joinedload(KnowledgeBaseCategoryDB.status),
        #    joinedload(KnowledgeBaseCategoryDB.type),
        #    joinedload(KnowledgeBaseCategoryDB.source),
        #
        #)
    )
    queries = result.scalars().all()
    return queries


@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_db)):
    typeList = ['Proof of Payments', 'Savings', 'Shares', 'Penalties', 'Loans', 'Bank Transfers']
    typeId = 1
    
    for value in typeList:
        db_status = KnowledgeBaseCategoryDB(
            #personal details
            cat_name = value,
        )
        db.add(db_status)
        typeId += 1
        
    try:
        await db.commit()
        #await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to initialize knowledge base categories: f{e}")
    return {'succeeded': True, 'message': 'Knowledge base categories have been successfully initialized'}



@router.get("/{cat_id}", response_model=KnowledgeBaseCategory)
async def get_knowledgebase_category(cat_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeBaseCategoryDB)
        #.options(
        #    joinedload(KnowledgeBaseCategoryDB.post),
        #    joinedload(KnowledgeBaseCategoryDB.status),
        #    joinedload(KnowledgeBaseCategoryDB.type),
        #    joinedload(KnowledgeBaseCategoryDB.source),
        #
        #)
        .filter(KnowledgeBaseCategoryDB.id == cat_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Unable to find knowledge base category with id '{cat_id}'")
    return category
