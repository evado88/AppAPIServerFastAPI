from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from helpers.http_client import init_client, close_client
from apps.osawe import osaweapp
from apps.lwsc import lwscapp

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Application starting up new...")
    yield
    # Shutdown logic
    print("Application shutting down new...")

origins = [
        "http://127.0.0.1",
        "http://localhost",
        "http://localhost:5173",
        "http://osawe.space",
        "https://osawe.space"
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

# SSL
'''
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.api-zm.online", "www.api-zm.online"]
)
'''


# include routers
# osawe
# osaweapp.include_osawe_routes(app)
# lwsc
lwscapp.include_lwsc_routes(app)

# create tables at startup

@app.on_event("startup")
async def startup():
    await init_client()
    #osawe
    #osaweapp.init_osawe_db(app)
    #lwsc
    lwscapp.init_lwsc_db(app)
        
@app.on_event("shutdown")
async def shutdown_event():
    await close_client()
    
def get_httpsx_client():
    return app.state.client