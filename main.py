from fastapi import FastAPI
from database import engine, Base
from routes import status_type_routes, transaction_routes, transaction_source_routes
from routes import transaction_type_routes, user_routes
from routes import monthly_posting_routes, config_routes, auth_routes
from routes import announcement_routes, notification_routes
from routes import member_query_routes, member_query_type_routes
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware


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


# create tables at startup


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        print("Application starting up old...")
        await conn.run_sync(Base.metadata.create_all)
