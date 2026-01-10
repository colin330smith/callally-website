"""
CallAlly API - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database.connection import engine, Base
from routers import auth_router, onboarding_router, business_router, webhooks_router
import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created")
    yield
    # Shutdown
    await engine.dispose()
    print("Database connection closed")


app = FastAPI(
    title="CallAlly API",
    description="AI Receptionist Platform for Home Service Businesses",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://callallynow.com",
        "https://www.callallynow.com",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",  # Live Server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(business_router)
app.include_router(webhooks_router)


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
    """Health check for Railway."""
    return {"status": "ok"}


@app.post("/api/admin/reset-db")
async def reset_database():
    """Drop and recreate all tables. USE WITH CAUTION - deletes all data!"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"status": "ok", "message": "Database tables recreated"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(config.PORT),
        reload=True
    )
