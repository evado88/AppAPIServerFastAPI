from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from helpers.http_client import init_client, close_client
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from apps.osawe import osaweapp
from apps.lwsc import lwscapp
import logging

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
        "https://osawe.space",
        "http://lpwsc.zam-services.online"
    ]


app = FastAPI(title="API System [FastAPI/PostgreSQL]")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    logger.error(f"Body received: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
    
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
osaweapp.include_osawe_routes(app)
# lwsc
#lwscapp.include_lwsc_routes(app)

# create tables at startup

@app.on_event("startup")
async def startup():
    await init_client()
    #osawe
    await osaweapp.init_osawe_db(app)
    #lwsc
    await lwscapp.init_lwsc_db(app)
        
@app.on_event("shutdown")
async def shutdown_event():
    await close_client()
    
def get_httpsx_client():
    return app.state.client