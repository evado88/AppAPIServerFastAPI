from apps.ccl.ccldb import engine, Base

from apps.ccl.routes import auth_routes
from apps.ccl.routes import user_routes
from apps.ccl.routes import lab_routes
from apps.ccl.routes import test_routes
from apps.ccl.routes import instrument_routes
from apps.ccl.routes import reagent_routes
from apps.ccl.routes import dashboard_routes
from apps.ccl.routes import data_routes

APP_ROUTE = "/ccl"

def include_ccl_routes(app):
    
    app.include_router(user_routes.router, prefix=APP_ROUTE)
    app.include_router(auth_routes.router, prefix=APP_ROUTE)
    app.include_router(lab_routes.router, prefix=APP_ROUTE)
    app.include_router(test_routes.router, prefix=APP_ROUTE)
    app.include_router(instrument_routes.router, prefix=APP_ROUTE)
    app.include_router(reagent_routes.router, prefix=APP_ROUTE)
    app.include_router(dashboard_routes.router, prefix=APP_ROUTE)
    app.include_router(data_routes.router, prefix=APP_ROUTE)
    
async def init_ccl_db(app):
    async with engine.begin() as conn:
        print("Application CCL starting up old...")
        await conn.run_sync(Base.metadata.create_all)