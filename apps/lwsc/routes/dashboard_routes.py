import calendar
from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy import func
from apps.lwsc import lwscapp
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.category_model import CategoryDB
from apps.lwsc.models.customer_model import CustomerDB
from apps.lwsc.models.district_model import DistrictDB
from apps.lwsc.models.meter_reading_model import (
    MeterReading,
    MeterReadingDB,
    MeterReadingWithDetail,
)
from apps.lwsc.models.param_models import (
    ParamChartItem,
    ParamDashboardStatistic,
    ParamDashboardYearSummary,
)
from apps.lwsc.models.user_model import UserDB
from apps.lwsc.models.walkroute_model import WalkRouteDB
from helpers import assist
import random
from sqlalchemy.orm import noload

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


@router.get("/year-to-date/{year}", response_model=ParamDashboardYearSummary)
async def get_ytd_dashboard(year: int, db: AsyncSession = Depends(get_lwsc_db)):
    print("starting ytd dashboard summary", assist.get_current_date(False))

    # get base series
    series = [
        "Consumption (M3)",
        "Revenue (ZMW)",
        "Consumption Daily (AVG)",
        "Consumption Per Day AVG (M3)",
        "Count",
    ]

    # get months
    months = list(calendar.month_name)[1:]

    monthData = []

    for serie in series:
        monthSerieData = [
            ParamChartItem(type=serie, id=index + 1, name=month, value=0.0)
            for index, month in enumerate(months)
        ]

        monthData.extend(monthSerieData)

    # get all districts
    result = await db.execute(select(DistrictDB).options(noload("*")))
    districts = result.scalars().all()

    districtData = []

    for serie in series:
        districtSerieData = [
            ParamChartItem(type=serie, id=district.id, name=district.name, value=0.0)
            for district in districts
        ]

        districtData.extend(districtSerieData)

    # get all categories
    result = await db.execute(select(CategoryDB).options(noload("*")))
    categories = result.scalars().all()

    categoryData = []

    for serie in series:
        categorySerieData = [
            ParamChartItem(
                type=serie, id=category.id, name=category.cat_name, value=0.0
            )
            for category in categories
        ]

        categoryData.extend(categorySerieData)

    # get readings per month
    start_of_year = date(year, 1, 1)
    start_of_next_year = date(year + 1, 1, 1)

    stmt = (
        select(
            func.extract("month", MeterReadingDB.read_date).label("month"),
            func.count(MeterReadingDB.read_date).label("Count"),
            func.coalesce(func.sum(MeterReadingDB.consumption_m3), 0).label(
                "consumptionM3"
            ),
            func.coalesce(func.sum(MeterReadingDB.consumption_zmw), 0).label(
                "consumptionZMW"
            ),
            func.coalesce(func.avg(MeterReadingDB.consumption_daily), 0).label(
                "consumptionDaily"
            ),
            func.coalesce(func.avg(MeterReadingDB.consumption_days), 0).label(
                "consumptionDays"
            ),
        )
        .where(
            MeterReadingDB.status_id == lwscapp.APPROVAL_STAGE_APPROVED,
            MeterReadingDB.read_date >= start_of_year,
            MeterReadingDB.read_date < start_of_next_year,
        )
        .group_by(func.extract("month", MeterReadingDB.read_date).label("month"))
    )

    result = await db.execute(stmt)
    rows = result.all()

    # map months
    for category in monthData:
        for row in rows:
            if category.id == row["month"]:
                if category.type == "Consumption (M3)":
                    category.value = round(row["consumptionM3"], 2)

                elif category.type == "Revenue (ZMW)":
                    category.value = round(row["consumptionZMW"], 2)

                elif category.type == "Consumption Daily (AVG)":
                    category.value = round(row["consumptionDaily"], 2)

                elif category.type == "Consumption Per Day AVG (M3)":
                    category.value = round(row["consumptionDays"], 2)
                    
                elif category.type == "Count":
                    category.value = row["Count"]

    # get readings per district
    start_of_year = date(year, 1, 1)
    start_of_next_year = date(year + 1, 1, 1)

    stmt = (
        select(
            CustomerDB.district_id,
            func.count(CustomerDB.district_id).label("Count"),
            func.coalesce(func.sum(MeterReadingDB.consumption_m3), 0).label(
                "consumptionM3"
            ),
            func.coalesce(func.sum(MeterReadingDB.consumption_zmw), 0).label(
                "consumptionZMW"
            ),
            func.coalesce(func.avg(MeterReadingDB.consumption_daily), 0).label(
                "consumptionDaily"
            ),
            func.coalesce(func.avg(MeterReadingDB.consumption_days), 0).label(
                "consumptionDays"
            ),
        )
        .join(CustomerDB, MeterReadingDB.customer_id == CustomerDB.id)
        .where(
            MeterReadingDB.status_id == lwscapp.APPROVAL_STAGE_APPROVED,
            MeterReadingDB.read_date >= start_of_year,
            MeterReadingDB.read_date < start_of_next_year,
        )
        .group_by(CustomerDB.district_id)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # map districts
    for category in districtData:
        for row in rows:
            if category.id == row["district_id"]:
                if category.type == "Consumption (M3)":
                    category.value = round(row["consumptionM3"], 2)

                elif category.type == "Revenue (ZMW)":
                    category.value = round(row["consumptionZMW"], 2)

                elif category.type == "Consumption Daily (AVG)":
                    category.value = round(row["consumptionDaily"], 2)

                elif category.type == "Consumption Per Day AVG (M3)":
                    category.value = round(row["consumptionDays"], 2)
                    
                elif category.type == "Count":
                    category.value = row["Count"]

    # get readings per category
    start_of_year = date(year, 1, 1)
    start_of_next_year = date(year + 1, 1, 1)

    stmt = (
        select(
            CustomerDB.cat_id,
            func.count(CustomerDB.cat_id).label("Count"),
            func.coalesce(func.sum(MeterReadingDB.consumption_m3), 0).label(
                "consumptionM3"
            ),
            func.coalesce(func.sum(MeterReadingDB.consumption_zmw), 0).label(
                "consumptionZMW"
            ),
            func.coalesce(func.avg(MeterReadingDB.consumption_daily), 0).label(
                "consumptionDaily"
            ),
            func.coalesce(func.avg(MeterReadingDB.consumption_days), 0).label(
                "consumptionDays"
            ),
        )
        .join(CustomerDB, MeterReadingDB.customer_id == CustomerDB.id)
        .where(
            MeterReadingDB.status_id == lwscapp.APPROVAL_STAGE_APPROVED,
            MeterReadingDB.read_date >= start_of_year,
            MeterReadingDB.read_date < start_of_next_year,
        )
        .group_by(CustomerDB.cat_id)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # map categories
    for category in categoryData:
        for row in rows:
            if category.id == row["cat_id"]:
                if category.type == "Consumption (M3)":
                    category.value = round(row["consumptionM3"], 2)

                elif category.type == "Revenue (ZMW)":
                    category.value = round(row["consumptionZMW"], 2)

                elif category.type == "Consumption Daily (AVG)":
                    category.value = round(row["consumptionDaily"], 2)

                elif category.type == "Consumption Per Day AVG (M3)":
                    category.value = round(row["consumptionDays"], 2)
                    
                elif category.type == "Count":
                    category.value = row["Count"]

    statisticData = []

    # get users
    stmt = select(func.count(UserDB.id)).where(
        UserDB.status_id == lwscapp.APPROVAL_STAGE_APPROVED
    )
    user_count = await db.scalar(stmt)
    # add
    statisticData.append(
        ParamDashboardStatistic(name="Users", value=user_count, color="green")
    )

    # get districts
    stmt = select(func.count(DistrictDB.id)).where(
        DistrictDB.status_id == lwscapp.APPROVAL_STAGE_APPROVED
    )
    district_count = await db.scalar(stmt)
    # add
    statisticData.append(
        ParamDashboardStatistic(name="Districts", value=district_count, color="red")
    )

    # get routes
    stmt = select(func.count(WalkRouteDB.id)).where(
        WalkRouteDB.status_id == lwscapp.APPROVAL_STAGE_APPROVED
    )
    route_count = await db.scalar(stmt)
    # add
    statisticData.append(
        ParamDashboardStatistic(name="Routes", value=route_count, color="orange")
    )

    # get customers
    stmt = select(func.count(CustomerDB.id)).where(
        CustomerDB.status_id == lwscapp.APPROVAL_STAGE_APPROVED
    )
    customer_count = await db.scalar(stmt)
    # add
    statisticData.append(
        ParamDashboardStatistic(name="Customers", value=customer_count, color="red")
    )

    # get meter readings
    stmt = select(func.count(MeterReadingDB.id)).where(
        MeterReadingDB.status_id == lwscapp.APPROVAL_STAGE_APPROVED
    )
    readings_count = await db.scalar(stmt)
    # add
    statisticData.append(
        ParamDashboardStatistic(
            name="Meter Readings", value=readings_count, color="green"
        )
    )

    categoriesCountData = [
        category for category in categoryData if category.type == "Count"
    ]

    print("ending ytd dashboard summary", assist.get_current_date(False))

    dashboard = ParamDashboardYearSummary(
        statistics=statisticData,
        months=monthData,
        districts=districtData,
        categories=categoryData,
        categoriesCount=categoriesCountData,
    )

    return dashboard
