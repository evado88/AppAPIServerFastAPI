from typing import List

from apps.lwsc.lwscdb import engine, Base

from apps.lwsc.models.bill_rate_model import BillRate
from apps.lwsc.routes import auth_routes
from apps.lwsc.routes import user_routes
from apps.lwsc.routes import walkroute_routes
from apps.lwsc.routes import customer_routes
from apps.lwsc.routes import meter_routes
from apps.lwsc.routes import meter_reading_routes
from apps.lwsc.routes import attachment_routes
from apps.lwsc.routes import category_routes
from apps.lwsc.routes import review_stages_routes
from apps.lwsc.routes import status_type_routes
from apps.lwsc.routes import district_routes
from apps.lwsc.routes import config_routes
from apps.lwsc.routes import user_role_routes
from apps.lwsc.routes import bill_rate_routes
from apps.lwsc.routes import meter_status_routes
from apps.lwsc.routes import dashboard_routes
from apps.lwsc.routes import transaction_type_routes
from apps.lwsc.routes import transaction_group_routes
from apps.lwsc.routes import transaction_routes


APP_ROUTE = "/lwsc"

STATUS_DRAFT = 1
STATUS_SUBMITTED = 2
STATUS_APPROVED = 4
STATUS_REJECTED = 5

APPROVAL_STAGE_DRAFT = 1
APPROVAL_STAGE_SUBMITTED = 2
APPROVAL_STAGE_UNDER_REVIEW = 3
APPROVAL_STAGE_APPROVED = 4
APPROVAL_STAGE_REJECTED = 5


def get_consumption_rate(consumption: float, rates: List[BillRate]):
    '''
    Gets the actual consumption based on billing bands
    '''
    
    total = 0.0
    
    # check if bill is within band
    for billrate in rates:
        if consumption > billrate.to_vol:
            total += billrate.rate
        else:
            break
    
    return total


def include_lwsc_routes(app):
    app.include_router(config_routes.router, prefix=APP_ROUTE)
    app.include_router(review_stages_routes.router, prefix=APP_ROUTE)
    app.include_router(status_type_routes.router, prefix=APP_ROUTE)
    app.include_router(user_role_routes.router, prefix=APP_ROUTE)

    app.include_router(user_routes.router, prefix=APP_ROUTE)
    app.include_router(attachment_routes.router, prefix=APP_ROUTE)
    app.include_router(auth_routes.router, prefix=APP_ROUTE)
    app.include_router(walkroute_routes.router, prefix=APP_ROUTE)

    app.include_router(district_routes.router, prefix=APP_ROUTE)
    app.include_router(bill_rate_routes.router, prefix=APP_ROUTE)
    app.include_router(category_routes.router, prefix=APP_ROUTE)
    app.include_router(customer_routes.router, prefix=APP_ROUTE)
    app.include_router(meter_routes.router, prefix=APP_ROUTE)
    app.include_router(meter_reading_routes.router, prefix=APP_ROUTE)
    app.include_router(meter_status_routes.router, prefix=APP_ROUTE)
    app.include_router(dashboard_routes.router, prefix=APP_ROUTE)
    
    app.include_router(transaction_routes.router, prefix=APP_ROUTE)
    app.include_router(transaction_type_routes.router, prefix=APP_ROUTE)
    app.include_router(transaction_group_routes.router, prefix=APP_ROUTE)

    
async def init_lwsc_db(app):
    async with engine.begin() as conn:
        print("Application lwsc starting up old...")
        await conn.run_sync(Base.metadata.create_all)