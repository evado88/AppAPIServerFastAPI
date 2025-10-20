from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.member_query_model import MemberQuery, MemberQueryDB, MemberQueryWithDetail
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
        type_id = mquery.type_id,
        # user
        user_id = mquery.user_id,
        # transaction
        title = mquery.title,
        content = mquery.content,
        # approval
        status_id = mquery.status_id,
        stage_id = mquery.stage_id,
        approval_levels = mquery.approval_levels,
        # service
        created_by=mquery.created_by,
    )
    db.add(db_tran)
    try:
        await db.commit()
        await db.refresh(db_tran)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create member query: {e}")
    return db_tran


@router.get("/list", response_model=List[MemberQueryWithDetail])
async def list_memberquerys(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MemberQueryDB)
        #.options(
        #    joinedload(MemberQueryDB.post),
        #    joinedload(MemberQueryDB.status),
        #    joinedload(MemberQueryDB.type),
        #    joinedload(MemberQueryDB.source),
        #
        #)
    )
    queries = result.scalars().all()
    return queries


@router.get("/id/{memberquery_id}", response_model=MemberQueryWithDetail)
async def get_memberquery(memberquery_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MemberQueryDB)
        #.options(
        #    joinedload(MemberQueryDB.post),
        #    joinedload(MemberQueryDB.status),
        #    joinedload(MemberQueryDB.type),
        #    joinedload(MemberQueryDB.source),
        #
        #)
        .filter(MemberQueryDB.id == memberquery_id)
    )
    query = result.scalars().first()
    if not query:
        raise HTTPException(status_code=404, detail=f"Unable to find member query with id '{memberquery_id}'")
    return query


@router.put("/update/{query_id}", response_model=MemberQueryWithDetail)
async def update_configuration(query_id: int, config_update: MemberQuery, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MemberQueryDB)
        .where(MemberQueryDB.id == query_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Unable to find member query with id '{query_id}'")
    
    # Update fields that are not None
    for key, value in config_update.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
        
    try:
        await db.commit()
        await db.refresh(config)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update member query {e}")
    return config


@router.get("/user/{user_id}", response_model=List[MemberQueryWithDetail])
async def list_user_memberquery(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MemberQueryDB)
        #.options(
        #    joinedload(MemberQueryDB.post),
        #    joinedload(MemberQueryDB.status),
        #    joinedload(MemberQueryDB.type),
        #    joinedload(MemberQueryDB.source),
        #
        #)
        .filter(MemberQueryDB.user_id == user_id)
    )
    queries = result.scalars().all()
    return queries

