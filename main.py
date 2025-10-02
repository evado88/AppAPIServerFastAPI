from fastapi import FastAPI
from database import engine, Base
from routes import statustyperoutes, transactionroutes, userroutes, transactiontyperoutes, transactionsourceroutes
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
app.include_router(statustyperoutes.router)
app.include_router(transactiontyperoutes.router)
app.include_router(transactionsourceroutes.router)
app.include_router(userroutes.router)
app.include_router(transactionroutes.router)

# create tables at startup


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        print("Application starting up old...")
        await conn.run_sync(Base.metadata.create_all)
