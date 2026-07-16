from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import router as api_router
from app.database.init_db import init_db

app = FastAPI(
    title="AI-First CRM HCP Module API",
    description="Backend API for managing HCPs, logging interactions, and agent capabilities.",
    version="1.0.0"
)

# CORS configuration
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*"  # Allow wildcard origin for local testing/dev
]

# We need to filter CORS based on config
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to auto-initialize DB and table structure
@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health_check():
    from datetime import datetime
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "database": settings.DATABASE_URL.split("://")[0]
    }

# Include API Router
app.include_router(api_router, prefix="/api")
