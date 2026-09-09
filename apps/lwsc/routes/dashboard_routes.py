import calendar
from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy import distinct, func
from apps.lwsc import lwscapp
from apps.lwsc.lwscdb import get_lwsc_db
from apps.lwsc.models.customer_category_model import CategoryDB
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
    ParamDistrictProgress,
    ParamMeterReaderProgress,
)
from apps.lwsc.models.reader_walkroute_model import MeterReaderWalkRouteDB
from apps.lwsc.models.user_model import UserDB
from apps.lwsc.models.walkroute_model import WalkRouteDB
from helpers import assist
import random
from sqlalchemy.orm import noload

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


def get_reading_summary_columns():
    """
    The aggregate columns shared by each of the year summary breakdowns
    """
    return [
        func.count(MeterReadingDB.id).label("count"),
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
    ]


def get_approved_count(model):
    """
    A scalar count of the approved records for the given table. Used so all of
    the dashboard counts can be read in a single trip to the database
    """
    return (
        select(func.count(model.id))
        .where(model.status_id == lwscapp.STATUS_APPROVED)
        .scalar_subquery()
    )


def apply_series_values(items, rows, key):
    """
    Copies the aggregated values onto the chart items. The rows are indexed on
    the grouping key first so each item is a single lookup rather than a scan
    over every row
    """
    values = {int(row._mapping[key]): row._mapping for row in rows}

    for item in items:
        row = values.get(item.id)

        if row is None:
            # nothing was aggregated for this month, district or category
            continue

        if item.type == "Consumption (M3)":
            item.value = round(row["consumptionM3"], 2)

        elif item.type == "Revenue (ZMW)":
            item.value = round(row["consumptionZMW"], 2)

        elif item.type == "Consumption Daily (AVG)":
            item.value = round(row["consumptionDaily"], 2)

        elif item.type == "Consumption Per Day AVG (M3)":
            item.value = round(row["consumptionDays"], 2)

        elif item.type == "Count":
            item.value = row["count"]


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

    # get all districts. Only the id and name are needed to build the series
    result = await db.execute(select(DistrictDB.id, DistrictDB.name))
    districts = result.all()

    districtData = []

    for serie in series:
        districtSerieData = [
            ParamChartItem(type=serie, id=district.id, name=district.name, value=0.0)
            for district in districts
        ]

        districtData.extend(districtSerieData)

    # get all categories
    result = await db.execute(select(CategoryDB.id, CategoryDB.cat_name))
    categories = result.all()

    categoryData = []

    for serie in series:
        categorySerieData = [
            ParamChartItem(
                type=serie, id=category.id, name=category.cat_name, value=0.0
            )
            for category in categories
        ]

        categoryData.extend(categorySerieData)

    # the year being reported on. Readings are filtered on a range rather than
    # on the year so the index on the period date can be used
    startOfYear = date(year, 1, 1)
    startOfNextYear = date(year + 1, 1, 1)

    # the summary is reported on the period the reading belongs to and not the
    # date it was taken, so a reading captured late still counts towards the
    # month it was raised for.
    # only approved readings count towards the summary. A reading that has only
    # been raised for a meter reader has no consumption on it yet
    readingFilter = (
        MeterReadingDB.status_id == lwscapp.STATUS_APPROVED,
        MeterReadingDB.period_date >= startOfYear,
        MeterReadingDB.period_date < startOfNextYear,
    )

    monthColumn = func.extract("month", MeterReadingDB.period_date).label("month")

    # get readings per month
    result = await db.execute(
        select(monthColumn, *get_reading_summary_columns())
        .where(*readingFilter)
        .group_by(monthColumn)
    )

    apply_series_values(monthData, result.all(), "month")

    # get readings per district
    result = await db.execute(
        select(CustomerDB.district_id, *get_reading_summary_columns())
        .join(CustomerDB, MeterReadingDB.customer_id == CustomerDB.id)
        .where(*readingFilter)
        .group_by(CustomerDB.district_id)
    )

    apply_series_values(districtData, result.all(), "district_id")

    # get readings per category
    result = await db.execute(
        select(CustomerDB.cat_id, *get_reading_summary_columns())
        .join(CustomerDB, MeterReadingDB.customer_id == CustomerDB.id)
        .where(*readingFilter)
        .group_by(CustomerDB.cat_id)
    )

    apply_series_values(categoryData, result.all(), "cat_id")

    # get all of the headline counts in one trip to the database
    result = await db.execute(
        select(
            get_approved_count(UserDB),
            get_approved_count(DistrictDB),
            get_approved_count(WalkRouteDB),
            get_approved_count(CustomerDB),
            get_approved_count(MeterReadingDB),
        )
    )

    (
        user_count,
        district_count,
        route_count,
        customer_count,
        readings_count,
    ) = result.one()

    statisticData = [
        ParamDashboardStatistic(name="Users", value=user_count, color="green"),
        ParamDashboardStatistic(name="Districts", value=district_count, color="red"),
        ParamDashboardStatistic(name="Routes", value=route_count, color="orange"),
        ParamDashboardStatistic(name="Customers", value=customer_count, color="red"),
        ParamDashboardStatistic(
            name="Meter Readings", value=readings_count, color="green"
        ),
    ]

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


@router.get(
    "/meter-reader-progress/{year}/{month}",
    response_model=List[ParamMeterReaderProgress],
)
async def get_meter_reader_progress(
    year: int, month: int, db: AsyncSession = Depends(get_lwsc_db)
):
    """
    Shows how far each meter reader has got with the readings raised for the
    period so management can see who is still outstanding.
    """

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400, detail=f"The month '{month}' is not a valid month"
        )

    # work out the period range. Readings are filtered on a range rather than an
    # exact date because a submitted reading can carry any day in the month
    periodStart = date(year, month, 1)
    periodEnd = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    # readings raised for each reader in the period. A reading that has only
    # been raised has no current value yet, which is what separates the
    # readings still awaiting submission from the ones actually taken
    readingStats = (
        select(
            MeterReadingDB.user_id.label("user_id"),
            func.count(MeterReadingDB.id).label("readings_total"),
            func.count(MeterReadingDB.id)
            .filter(MeterReadingDB.current.is_(None))
            .label("readings_awaiting"),
            func.count(MeterReadingDB.id)
            .filter(MeterReadingDB.current.is_not(None))
            .label("readings_submitted"),
            func.count(MeterReadingDB.id)
            .filter(MeterReadingDB.status_id == lwscapp.STATUS_APPROVED)
            .label("readings_approved"),
            func.max(MeterReadingDB.read_date)
            .filter(MeterReadingDB.current.is_not(None))
            .label("last_read_date"),
        )
        .where(
            MeterReadingDB.period_date >= periodStart,
            MeterReadingDB.period_date < periodEnd,
        )
        .group_by(MeterReadingDB.user_id)
        .subquery()
    )

    # how many routes each reader is assigned to
    routeStats = (
        select(
            MeterReaderWalkRouteDB.user_id.label("user_id"),
            func.count(MeterReaderWalkRouteDB.id).label("routes_assigned"),
        )
        .group_by(MeterReaderWalkRouteDB.user_id)
        .subquery()
    )

    # how many customers sit on those routes. This is the denominator for
    # the progress the reader has made
    customerStats = (
        select(
            MeterReaderWalkRouteDB.user_id.label("user_id"),
            func.count(CustomerDB.id).label("customers_assigned"),
        )
        .select_from(MeterReaderWalkRouteDB)
        .join(CustomerDB, CustomerDB.route_id == MeterReaderWalkRouteDB.route_id)
        .group_by(MeterReaderWalkRouteDB.user_id)
        .subquery()
    )

    # every meter reader is listed, including the ones that have done nothing
    result = await db.execute(
        select(
            UserDB.id,
            UserDB.code,
            UserDB.fname,
            UserDB.lname,
            UserDB.email,
            DistrictDB.name,
            func.coalesce(routeStats.c.routes_assigned, 0),
            func.coalesce(customerStats.c.customers_assigned, 0),
            func.coalesce(readingStats.c.readings_total, 0),
            func.coalesce(readingStats.c.readings_awaiting, 0),
            func.coalesce(readingStats.c.readings_submitted, 0),
            func.coalesce(readingStats.c.readings_approved, 0),
            readingStats.c.last_read_date,
        )
        .select_from(UserDB)
        .outerjoin(DistrictDB, DistrictDB.id == UserDB.district_id)
        .outerjoin(routeStats, routeStats.c.user_id == UserDB.id)
        .outerjoin(customerStats, customerStats.c.user_id == UserDB.id)
        .outerjoin(readingStats, readingStats.c.user_id == UserDB.id)
        .where(UserDB.role_id == lwscapp.ROLE_METERREADER)
        .order_by(UserDB.fname)
    )

    progress = []

    for row in result.all():
        (
            user_id,
            code,
            fname,
            lname,
            email,
            district_name,
            routes_assigned,
            customers_assigned,
            readings_total,
            readings_awaiting,
            readings_submitted,
            readings_approved,
            last_read_date,
        ) = row

        # the customers on the assigned routes are the target. Fall back to the
        # readings raised when the reader has no routes assigned yet
        target = customers_assigned if customers_assigned > 0 else readings_total

        percent = round((readings_submitted / target) * 100, 2) if target > 0 else 0.0

        progress.append(
            ParamMeterReaderProgress(
                # reader
                user_id=user_id,
                code=code,
                name=f"{fname} {lname}",
                email=email,
                district_name=district_name,
                # responsibility
                routes_assigned=routes_assigned,
                customers_assigned=customers_assigned,
                # period
                readings_total=readings_total,
                readings_awaiting=readings_awaiting,
                readings_submitted=readings_submitted,
                readings_approved=readings_approved,
                # progress
                progress_percent=percent,
                last_read_date=last_read_date,
            )
        )

    return progress


@router.get(
    "/district-progress/{year}/{month}",
    response_model=List[ParamDistrictProgress],
)
async def get_district_progress(
    year: int, month: int, db: AsyncSession = Depends(get_lwsc_db)
):
    """
    Shows how far each district has got with the readings raised for the period
    so management can see which areas are still outstanding.
    """

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400, detail=f"The month '{month}' is not a valid month"
        )

    # work out the period range. Readings are filtered on a range rather than an
    # exact date because a submitted reading can carry any day in the month
    periodStart = date(year, month, 1)
    periodEnd = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    # readings raised in the period for each district. The district is taken
    # from the customer rather than the name held on the reading so the count
    # always lines up with the customers counted below
    readingStats = (
        select(
            CustomerDB.district_id.label("district_id"),
            func.count(MeterReadingDB.id).label("readings_total"),
            func.count(MeterReadingDB.id)
            .filter(MeterReadingDB.current.is_(None))
            .label("readings_awaiting"),
            func.count(MeterReadingDB.id)
            .filter(MeterReadingDB.current.is_not(None))
            .label("readings_submitted"),
            func.count(MeterReadingDB.id)
            .filter(MeterReadingDB.status_id == lwscapp.STATUS_APPROVED)
            .label("readings_approved"),
            func.max(MeterReadingDB.read_date)
            .filter(MeterReadingDB.current.is_not(None))
            .label("last_read_date"),
        )
        .select_from(MeterReadingDB)
        .join(CustomerDB, CustomerDB.id == MeterReadingDB.customer_id)
        .where(
            MeterReadingDB.period_date >= periodStart,
            MeterReadingDB.period_date < periodEnd,
        )
        .group_by(CustomerDB.district_id)
        .subquery()
    )

    # how many routes make up each district
    routeStats = (
        select(
            WalkRouteDB.district_id.label("district_id"),
            func.count(WalkRouteDB.id).label("routes"),
        )
        .group_by(WalkRouteDB.district_id)
        .subquery()
    )

    # how many customers sit in each district. This is the denominator for
    # the progress the district has made
    customerStats = (
        select(
            CustomerDB.district_id.label("district_id"),
            func.count(CustomerDB.id).label("customers"),
        )
        .group_by(CustomerDB.district_id)
        .subquery()
    )

    # how many meter readers are working the routes in each district
    readerStats = (
        select(
            WalkRouteDB.district_id.label("district_id"),
            func.count(distinct(MeterReaderWalkRouteDB.user_id)).label(
                "readers_assigned"
            ),
        )
        .select_from(MeterReaderWalkRouteDB)
        .join(WalkRouteDB, WalkRouteDB.id == MeterReaderWalkRouteDB.route_id)
        .group_by(WalkRouteDB.district_id)
        .subquery()
    )

    # every district is listed, including the ones with nothing raised yet
    result = await db.execute(
        select(
            DistrictDB.id,
            DistrictDB.name,
            DistrictDB.code,
            func.coalesce(routeStats.c.routes, 0),
            func.coalesce(readerStats.c.readers_assigned, 0),
            func.coalesce(customerStats.c.customers, 0),
            func.coalesce(readingStats.c.readings_total, 0),
            func.coalesce(readingStats.c.readings_awaiting, 0),
            func.coalesce(readingStats.c.readings_submitted, 0),
            func.coalesce(readingStats.c.readings_approved, 0),
            readingStats.c.last_read_date,
        )
        .select_from(DistrictDB)
        .outerjoin(routeStats, routeStats.c.district_id == DistrictDB.id)
        .outerjoin(readerStats, readerStats.c.district_id == DistrictDB.id)
        .outerjoin(customerStats, customerStats.c.district_id == DistrictDB.id)
        .outerjoin(readingStats, readingStats.c.district_id == DistrictDB.id)
        .order_by(DistrictDB.name)
    )

    progress = []

    for row in result.all():
        (
            district_id,
            name,
            code,
            routes,
            readers_assigned,
            customers,
            readings_total,
            readings_awaiting,
            readings_submitted,
            readings_approved,
            last_read_date,
        ) = row

        # the customers in the district are the target. Fall back to the
        # readings raised when the district has no customers loaded yet
        target = customers if customers > 0 else readings_total

        percent = round((readings_submitted / target) * 100, 2) if target > 0 else 0.0

        progress.append(
            ParamDistrictProgress(
                # district
                district_id=district_id,
                name=name,
                code=code,
                # make up
                routes=routes,
                readers_assigned=readers_assigned,
                customers=customers,
                # period
                readings_total=readings_total,
                readings_awaiting=readings_awaiting,
                readings_submitted=readings_submitted,
                readings_approved=readings_approved,
                # progress
                progress_percent=percent,
                last_read_date=last_read_date,
            )
        )

    return progress
