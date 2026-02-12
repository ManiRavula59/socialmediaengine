from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from .database import engine
from .models import Base
from .routes import overview
from .routes import insights
from .routes import search
from .routes.semantic_search import router as semantic_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Social Media Insight Engine",
    description="Multi-Model LLM Validation System for Twitter Analytics with 500K tweets",
    version="1.0.0"
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers
app.include_router(overview.router)
app.include_router(insights.router)
app.include_router(search.router)
app.include_router(semantic_router)  # ✅ This adds /api/ask and /api/explore endpoints

@app.get("/")
async def root():
    """Root endpoint - shows API status and available models"""
    return {
        "message": "Social Media Insight Engine API",
        "status": "running",
        "models": [
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "stepfun/step-3.5-flash:free",
            "arcee-ai/trinity-large-preview:free",
            "arcee-ai/trinity-mini:free"
        ],
        "total_tweets_indexed": 500000,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Optional: Add a debug endpoint to see all registered routes
@app.get("/api/routes")
async def list_routes():
    """Debug endpoint to see all registered routes"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else []
        })
    return {"routes": routes}