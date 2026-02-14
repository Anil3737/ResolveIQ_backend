# app/main.py

from fastapi import FastAPI
from app.database import Base, engine
from app.models import Role, User  # ensures models load
from app.routes.auth_routes import router as auth_router
from app.routes.admin_routes import router as admin_router
from app.routes import ticket_router
# AI router disabled until dependencies are installed
# from app.ai import ai_router



app = FastAPI(title="ResolveIQ API")

# Create tables - NOTE: Tables should be created using create_tables.py or alembic migrations
# Commenting out to avoid blocking server startup
# Base.metadata.create_all(bind=engine)

# Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(ticket_router)
# AI router disabled until dependencies are installed (sentence-transformers, sklearn)
# app.include_router(ai_router, prefix="/api/v1")

@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "Welcome to ResolveIQ API",
        "version": "1.0",
        "docs": "http://127.0.0.1:8000/docs",
        "health_check": "http://127.0.0.1:8000/api/v1/health"
    }


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "ResolveIQ API"}
