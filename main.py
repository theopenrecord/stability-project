"""
Northwoods Housing Security Resource API
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import resources
from app.database import check_db_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Northwoods Housing Resource API...")
    if check_db_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed - check DATABASE_URL environment variable")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Northwoods Housing Security Resource API",
    description="API for housing security resources across Northern Michigan",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Northwoods Housing Security Resource API",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    db_status = "connected" if check_db_connection() else "disconnected"
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "timestamp": "2025-11-07"
    }

# Route registration
app.include_router(resources.router, prefix="/api/resources", tags=["resources"])

# Will add more routers as we build
# app.include_router(users.router, prefix="/api/users", tags=["users"])
# app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
