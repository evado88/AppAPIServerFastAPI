import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from apps.osawe.osawedb import get_osawe_db
from apps.osawe.models.department_model import Department, DepartmentDB

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("/create", response_model=Department)
async def post_department(department: Department, db: AsyncSession = Depends(get_osawe_db)):


    db_context = DepartmentDB(
        # update
        
        description=department.description,
        name=department.name,
        description=department.description,
        description=department.description,
        description=department.description,
        description=department.description,
    )
    db.add(db_context)
    try:
        await db.commit()
        await db.refresh(db_context)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not create department: {e}")

    return db_context


@router.get("/list", response_model=List[Department])
async def list_departments(db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(
        select(
            DepartmentDB
        )
    )
    departments = result.scalars().all()
    return departments

@router.put("/update/{id}", response_model=Department)
async def update_department(
    id: int, department_update: Department, db: AsyncSession = Depends(get_osawe_db)
):
    result = await db.execute(select(DepartmentDB).where(DepartmentDB.id == id))
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to find department with id '{id}'",
        )

    # Update fields that are not None
    for key, value in department_update.dict(exclude_unset=True).items():
        setattr(department, key, value)

    try:
        await db.commit()
        await db.refresh(department)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Unable to update department {e}")
    return department


@router.get("/id/{id}", response_model=Department)
async def get_department(id: int, db: AsyncSession = Depends(get_osawe_db)):
    result = await db.execute(
        select(DepartmentDB)
        .filter(DepartmentDB.id == id)
    )
    department = result.scalars().first()
    if not department:
        raise HTTPException(
            status_code=404, detail=f"Unable to find 'department with id '{id}' not found"
        )

    return department