from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.user_role_model import UserRole, UserRoleDB

router = APIRouter(prefix="/user-roles", tags=["Roles"])


@router.post("/create", response_model=UserRole)
async def create_userrole(userrole: UserRole, db: AsyncSession = Depends(get_lwsc_db)):
    
    db_user = UserRoleDB(
        #personal details
        id = userrole.id,
        role_name=userrole.role_name,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(userrole_code=400, detail=f"Unable to create user role: f{e}")
    return db_user

@router.post("/initialize")
async def initialize(db: AsyncSession = Depends(get_lwsc_db)):
    userroleList = ['Administrator', 'Meter Reader']
    userroleId = 1
    
    for value in userroleList:
        db_userrole = UserRoleDB(
            #personal details
            id = userroleId,
            role_name=value,
        )
        db.add(db_userrole)
        userroleId += 1
        
    try:
        await db.commit()
        #await db.refresh(db_userrole)
    except Exception as e:
        await db.rollback()
        raise HTTPException(userrole_code=400, detail=f"Unable to initialize user roles: f{e}")
    return {'succeeded': True, 'message': 'Roles have been successfully initialized'}


@router.get("/list", response_model=List[UserRole])
async def list_userrolees(db: AsyncSession = Depends(get_lwsc_db)):
    result = await db.execute(select(UserRoleDB))
    return result.scalars().all()

