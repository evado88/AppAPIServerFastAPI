from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.member_query_type_model import MemberQueryType, MemberQueryTypeDB

router = APIRouter(prefix="/member-query-types", tags=["MemberQueryTypes"])


@router.post("/create", response_model=MemberQueryType)
async def create_type(status: MemberQueryType, db: AsyncSession = Depends(get_db)):
    
    db_user = MemberQueryTypeDB(
        #personal details
        id = status.id,
        status_name=status.status_name,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to create member query type: f{e}")
    return db_user

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_db)):
    typeList = ['Account', 'Savings', 'Shares', 'Penalties', 'Loans']
    typeId = 1
    
    for value in typeList:
        db_status = MemberQueryTypeDB(
            #personal details
            id = typeId,
            query_type_name=value,
        )
        db.add(db_status)
        typeId += 1
        
    try:
        await db.commit()
        #await db.refresh(db_status)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to initialize member query types: f{e}")
    return {'succeeded': True, 'message': 'Member query types have been successfully initialized'}



@router.get("/list", response_model=List[MemberQueryType])
async def list_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MemberQueryTypeDB))
    return result.scalars().all()

