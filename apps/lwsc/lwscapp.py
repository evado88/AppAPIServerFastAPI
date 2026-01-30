from apps.osawe.osawedb import engine, Base

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
from apps.lwsc.routes import town_routes
from apps.lwsc.routes import config_routes
from apps.lwsc.routes import user_role_routes

APP_ROUTE = "/lwsc"

def include_lwsc_routes(app):
    app.include_router(config_routes.router, prefix=APP_ROUTE)
    app.include_router(review_stages_routes.router, prefix=APP_ROUTE)
    app.include_router(status_type_routes.router, prefix=APP_ROUTE)
    app.include_router(user_role_routes.router, prefix=APP_ROUTE)

    app.include_router(user_routes.router, prefix=APP_ROUTE)
    app.include_router(attachment_routes.router, prefix=APP_ROUTE)
    app.include_router(auth_routes.router, prefix=APP_ROUTE)
    app.include_router(walkroute_routes.router, prefix=APP_ROUTE)

    app.include_router(town_routes.router, prefix=APP_ROUTE)
    app.include_router(category_routes.router, prefix=APP_ROUTE)
    app.include_router(customer_routes.router, prefix=APP_ROUTE)
    app.include_router(meter_routes.router, prefix=APP_ROUTE)
    app.include_router(meter_reading_routes.router, prefix=APP_ROUTE)
    
async def init_lwsc_db(app):
    async with engine.begin() as conn:
        print("Application lwsc starting up old...")
        await conn.run_sync(Base.metadata.create_all)