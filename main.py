from fastapi import FastAPI
from database import engine, Base
from routes import status_type_routes, transaction_routes, transaction_source_routes
from routes import transaction_type_routes, user_routes
from routes import monthly_posting_routes, config_routes, auth_routes
from routes import announcement_routes, notification_routes
from routes import member_query_routes, member_query_type_routes
from routes import meeting_routes, attendance_routes, attendance_type_routes
from routes import member_routes, knowledge_base_category_routes, knowledge_base_routes
from routes import review_stages_routes
from routes import posting_period_routes
from routes import transaction_state_routes
from routes import penalty_type_routes
from routes import attachment_routes
from routes import whatsapp_routes
from routes import data_routes
from routes import transaction_group_routes
from routes import payment_method_routes
from routes import guarantor_routes

from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from helpers.http_client import init_client, close_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Application starting up new...")
    yield
    # Shutdown logic
    print("Application shutting down new...")

origins = [
        "http://localhost",
        "http://localhost:5173",
        "https://your-frontend-domain.com",
    ]


app = FastAPI(title="SACCO [FastAPI/PostgreSQL]")

app.mount("/static", StaticFiles(directory="uploads"), name="static")

#COR
app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],  # Allows all HTTP methods
        allow_headers=["*"],  # Allows all headers
    )

# include routers
app.include_router(status_type_routes.router)
app.include_router(transaction_type_routes.router)
app.include_router(penalty_type_routes.router)
app.include_router(transaction_state_routes.router)
app.include_router(transaction_source_routes.router)
app.include_router(user_routes.router)
app.include_router(transaction_routes.router)
app.include_router(monthly_posting_routes.router)
app.include_router(config_routes.router)
app.include_router(auth_routes.router)
app.include_router(member_query_type_routes.router)
app.include_router(member_query_routes.router)
app.include_router(announcement_routes.router)
app.include_router(notification_routes.router)
app.include_router(meeting_routes.router)
app.include_router(attendance_type_routes.router)
app.include_router(attendance_routes.router)
app.include_router(member_routes.router)
app.include_router(knowledge_base_category_routes.router)
app.include_router(knowledge_base_routes.router)
app.include_router(review_stages_routes.router)
app.include_router(posting_period_routes.router)
app.include_router(attachment_routes.router)
app.include_router(whatsapp_routes.router)
app.include_router(data_routes.router)
app.include_router(transaction_group_routes.router)
app.include_router(guarantor_routes.router)
app.include_router(payment_method_routes.router)
# create tables at startup


@app.on_event("startup")
async def startup():
    await init_client()
    async with engine.begin() as conn:
        print("Application starting up old...")
        await conn.run_sync(Base.metadata.create_all)
        
@app.on_event("shutdown")
async def shutdown_event():
    await close_client()
    
def get_httpsx_client():
    return app.state.client