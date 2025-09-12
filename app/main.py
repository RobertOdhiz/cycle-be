from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
from app.config import settings
from app.database import init_db
from app.routers import auth, bikes, docks, zones, rentals, payments, notifications, verification, admin, sync
from app.worker.celery import celery_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Cycle - Offline-first bicycle rental platform API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["*.cycle.com", "*.vercel.app", "*.fly.dev"]
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "Something went wrong",
            "request_id": request_id
        }
    )


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(bikes.router, prefix="/bikes", tags=["Bikes"])
app.include_router(docks.router, prefix="/docks", tags=["Docks"])
app.include_router(zones.router, prefix="/zones", tags=["Zones"])
app.include_router(rentals.router, prefix="/rides", tags=["Rentals"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(verification.router, prefix="/verification", tags=["Verification"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(sync.router, prefix="/sync", tags=["Sync"])


@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Welcome to Cycle API",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {
        "success": True,
        "status": "healthy",
        "timestamp": time.time()
    }


@app.get("/metrics")
async def metrics():
    # Basic metrics endpoint - can be enhanced with Prometheus
    return {
        "success": True,
        "metrics": {
            "uptime": time.time(),
            "version": settings.app_version
        }
    }
