"""
CallAlly API - FastAPI Application Entry Point
Production-ready with security hardening
"""
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from collections import defaultdict
from sqlalchemy import text
import time
import asyncio
import os

from database.connection import engine, Base
from routers import auth_router, onboarding_router, business_router, webhooks_router
import config


# ============================================================================
# RATE LIMITING
# ============================================================================
class RateLimiter:
    """Simple in-memory rate limiter."""
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = asyncio.Lock()

    async def is_rate_limited(
        self,
        key: str,
        max_requests: int = 60,
        window_seconds: int = 60
    ) -> bool:
        """Check if a key has exceeded rate limit."""
        async with self.lock:
            now = time.time()
            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < window_seconds
            ]
            # Check limit
            if len(self.requests[key]) >= max_requests:
                return True
            # Add current request
            self.requests[key].append(now)
            return False

rate_limiter = RateLimiter()


# ============================================================================
# APPLICATION SETUP
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables ready")
    print(f"✅ Running in {'PRODUCTION' if os.getenv('RAILWAY_ENVIRONMENT') else 'DEVELOPMENT'} mode")
    yield
    # Shutdown
    await engine.dispose()
    print("Database connection closed")


app = FastAPI(
    title="CallAlly API",
    description="AI Receptionist Platform for Home Service Businesses",
    version="1.0.0",
    lifespan=lifespan,
    # Disable docs in production for security
    docs_url="/docs" if not os.getenv("RAILWAY_ENVIRONMENT") else None,
    redoc_url="/redoc" if not os.getenv("RAILWAY_ENVIRONMENT") else None,
)


# ============================================================================
# SECURITY MIDDLEWARE
# ============================================================================

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting based on IP address."""
    # Get client IP
    client_ip = request.client.host
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    # Stricter limits for auth endpoints
    path = request.url.path
    if "/auth/login" in path or "/auth/signup" in path:
        max_requests, window = 10, 60  # 10 requests per minute for auth
    elif "/webhooks/" in path:
        max_requests, window = 200, 60  # Higher limit for webhooks
    else:
        max_requests, window = 100, 60  # 100 requests per minute default

    if await rate_limiter.is_rate_limited(client_ip, max_requests, window):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )

    response = await call_next(request)
    return response


# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests for monitoring."""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time

    # Log slow requests (>1s)
    if process_time > 1.0:
        print(f"⚠️ SLOW REQUEST: {request.method} {request.url.path} took {process_time:.2f}s")

    # Log errors
    if response.status_code >= 400:
        client_ip = request.headers.get("x-forwarded-for", request.client.host)
        print(f"❌ ERROR {response.status_code}: {request.method} {request.url.path} from {client_ip}")

    return response


# CORS configuration - restricted for production
ALLOWED_ORIGINS = [
    "https://callallynow.com",
    "https://www.callallynow.com",
]

# Add localhost origins only in development
if not os.getenv("RAILWAY_ENVIRONMENT"):
    ALLOWED_ORIGINS.extend([
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=600,  # Cache preflight for 10 minutes
)


# ============================================================================
# ROUTERS
# ============================================================================
app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(business_router)
app.include_router(webhooks_router)


# ============================================================================
# HEALTH CHECKS
# ============================================================================
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "CallAlly API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check for Railway with database verification."""
    try:
        # Quick database connectivity check
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected"}
        )


# ============================================================================
# ADMIN ENDPOINTS (Protected)
# ============================================================================
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")

@app.post("/api/admin/reset-db")
async def reset_database(request: Request):
    """
    Drop and recreate all tables.
    PROTECTED: Requires ADMIN_SECRET header.
    """
    # Verify admin secret
    provided_secret = request.headers.get("X-Admin-Secret", "")
    if not ADMIN_SECRET or provided_secret != ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized"
        )

    # Don't allow in production without explicit override
    if os.getenv("RAILWAY_ENVIRONMENT") and not request.headers.get("X-Force-Production"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot reset database in production without X-Force-Production header"
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print("⚠️ DATABASE RESET by admin")
    return {"status": "ok", "message": "Database tables recreated"}


# ============================================================================
# GLOBAL EXCEPTION HANDLER
# ============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    # Log the full error internally
    import traceback
    print(f"❌ Unhandled exception: {type(exc).__name__}: {exc}")
    print(traceback.format_exc())

    # Return generic error to client (don't expose internals)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(config.PORT),
        reload=True
    )
