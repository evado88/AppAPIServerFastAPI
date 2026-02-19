from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

from apps.ccl.ccldb import get_ccl_db
from apps.ccl.models.instrument_model import InstrumentDB
from apps.ccl.models.instrument_model import InstrumentDB
from apps.ccl.models.lab_model import LabDB
from apps.ccl.models.param_models import (
    ParamDashboard,
    ParamTestComponentDetail,
    ParamTestCost,
    ParamTestDetail,
)
from apps.ccl.models.reagent_model import ReagentDB
from apps.ccl.models.test_model import Test, TestDB, TestWithDetail
from apps.ccl.models.user_model import UserDB

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


async def updateInstrumentList(test: TestDB, db: AsyncSession):
    # get instruments
    result = await db.execute(select(InstrumentDB))
    instruments = result.scalars().all()

    # check loaded instruments against test instrument list and update with cost
    if test.instrument_list:
        for item in test.instrument_list:
            for instrument in instruments:
                if item["id"] == instrument.id:
                    item["name"] = instrument.name
                    item["total_cost"] = instrument.total_cost
                    item["annual_cost"] = instrument.total_cost
                    break

    return test.instrument_list


async def updateReagentList(test: TestDB, db: AsyncSession):
    # get reagents
    result = await db.execute(select(ReagentDB))
    reagents = result.scalars().all()

    # check loaded reagents against test reagent list and update with cost
    if test.reagent_list:
        for item in test.reagent_list:
            for reagent in reagents:
                if item["id"] == reagent.id:

                    testsWithin = (test.annual_total * reagent.expiry_period) / 365
                    testsUsable = min([testsWithin, reagent.tests_per_gru])
                    consumed = (
                        test.annual_total / testsUsable if testsUsable > 0 else 0
                    )
                    costPerUnit = (
                        consumed / test.annual_total if test.annual_total> 0 else 0
                    )
                    costPerTest = costPerUnit * reagent.cost
                    total_cost = costPerTest * test.annual_total

                    item["name"] = reagent.name
                    item["cost"] = reagent.cost
                    item["expiry_period"] = reagent.expiry_period
                    item["generic_reagent_unit"] = reagent.generic_reagent_unit
                    item["quantity_per_gru"] = reagent.quantity_per_gru
                    item["tests_per_grud"] = reagent.tests_per_gru
                    item["test_actual"] = test.annual_total
                    item["gru_consumed"] = consumed
                    item["cost_per_test"] = costPerTest
                    item["total_cost"] = total_cost
                    
                    break

    return test.reagent_list


@router.get("/test-costing", response_model=ParamDashboard)
async def get_test_dashboard(db: AsyncSession = Depends(get_ccl_db)):

    total_tests = await db.scalar(select(func.count()).select_from(TestDB))

    instruments = await db.scalar(select(func.count()).select_from(InstrumentDB))

    reagents = await db.scalar(select(func.count()).select_from(ReagentDB))

    users = await db.scalar(select(func.count()).select_from(UserDB))

    labs = await db.scalar(select(func.count()).select_from(LabDB))

    result = await db.execute(select(TestDB))
    tests = result.scalars().all()

    testCostList = []

    # update details for each test
    for test in tests:
        reagentList = await updateReagentList(test, db)
        instrumentList = await updateInstrumentList(test, db)
        
        totalReagentCost = sum(item["cost_per_test"] for item in reagentList)
        totalInstrumentCost = sum(item["annual_cost"] for item in instrumentList)
        actualInstrumentCost = totalInstrumentCost / test.annual_total
        
        testCost = ParamTestCost(
            name=test.name,
            lab=test.lab.name,
            annual_credit=test.annual_credit,
            annual_nhima=test.annual_nhima,
            annual_research =test.annual_research,
            annual_walkins=test.annual_walkins,
            annual_shift = test.annual_shift,
            annual_total=test.annual_total,
            total_cost=totalReagentCost + actualInstrumentCost,
            components=[
                ParamTestComponentDetail(
                    component="reagent", cost=totalReagentCost, items=reagentList
                ),
                ParamTestComponentDetail(
                    component="instrument", cost=actualInstrumentCost, items=instrumentList
                ),
            ],
        )

        testCostList.append(testCost)

    return ParamDashboard(
        total_tests=total_tests,
        total_labs=labs,
        total_instruments=instruments,
        total_reagents=reagents,
        total_users=users,
        tests=testCostList,
    )
