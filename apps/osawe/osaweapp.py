from apps.osawe.osawedb import engine, Base

from apps.osawe.routes import status_type_routes, transaction_routes, transaction_source_routes
from apps.osawe.routes import transaction_type_routes, user_routes
from apps.osawe.routes import monthly_posting_routes, config_routes, auth_routes
from apps.osawe.routes import announcement_routes, notification_routes
from apps.osawe.routes import member_query_routes, member_query_type_routes
from apps.osawe.routes import meeting_routes, attendance_routes, attendance_type_routes
from apps.osawe.routes import member_routes, knowledge_base_category_routes, knowledge_base_routes
from apps.osawe.routes import review_stages_routes
from apps.osawe.routes import posting_period_routes
from apps.osawe.routes import transaction_state_routes
from apps.osawe.routes import penalty_type_routes
from apps.osawe.routes import attachment_routes
from apps.osawe.routes import communication_channel_routes
from apps.osawe.routes import data_routes
from apps.osawe.routes import transaction_group_routes
from apps.osawe.routes import payment_method_routes
from apps.osawe.routes import guarantor_routes
from apps.osawe.routes import sensor_routes
from apps.osawe.routes import audit_routes

APP_ROUTE = "/osawe"

def include_osawe_routes(app):
    app.include_router(auth_routes.router, prefix=APP_ROUTE)
    app.include_router(config_routes.router, prefix=APP_ROUTE)
    app.include_router(user_routes.router, prefix=APP_ROUTE)
    app.include_router(status_type_routes.router, prefix=APP_ROUTE)
    app.include_router(transaction_type_routes.router, prefix=APP_ROUTE)
    app.include_router(transaction_source_routes.router, prefix=APP_ROUTE)
    app.include_router(transaction_state_routes.router, prefix=APP_ROUTE)
    app.include_router(transaction_group_routes.router, prefix=APP_ROUTE)
    app.include_router(penalty_type_routes.router, prefix=APP_ROUTE)
    app.include_router(review_stages_routes.router, prefix=APP_ROUTE)
    app.include_router(posting_period_routes.router, prefix=APP_ROUTE)
    app.include_router(monthly_posting_routes.router, prefix=APP_ROUTE)
    app.include_router(transaction_routes.router, prefix=APP_ROUTE)
    app.include_router(announcement_routes.router, prefix=APP_ROUTE)
    app.include_router(notification_routes.router, prefix=APP_ROUTE)
    app.include_router(member_query_type_routes.router, prefix=APP_ROUTE)
    app.include_router(member_query_routes.router, prefix=APP_ROUTE)
    app.include_router(member_routes.router, prefix=APP_ROUTE)
    app.include_router(knowledge_base_category_routes.router, prefix=APP_ROUTE)
    app.include_router(knowledge_base_routes.router, prefix=APP_ROUTE)
    app.include_router(meeting_routes.router, prefix=APP_ROUTE)
    app.include_router(attendance_type_routes.router, prefix=APP_ROUTE)
    app.include_router(attendance_routes.router, prefix=APP_ROUTE)
    app.include_router(attachment_routes.router, prefix=APP_ROUTE)
    app.include_router(communication_channel_routes.router, prefix=APP_ROUTE)
    app.include_router(data_routes.router, prefix=APP_ROUTE)
    app.include_router(payment_method_routes.router, prefix=APP_ROUTE)
    app.include_router(guarantor_routes.router, prefix=APP_ROUTE)
    app.include_router(sensor_routes.router, prefix=APP_ROUTE)
    app.include_router(audit_routes.router, prefix=APP_ROUTE)
    
async def init_osawe_db(app):
    async with engine.begin() as conn:
        print("Application osawe starting up old...")
        await conn.run_sync(Base.metadata.create_all)