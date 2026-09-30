import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.database import connect_to_mongo, close_mongo_connection
from app.api.auth import router as auth_router
from app.api.resume import router as resume_router
from app.api.questions import router as questions_router
from app.api.interview import router as interview_router
from app.api.websocket_router import router as ws_router
from app.services.cleanup_service import CleanupService
from app.utils.logger import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-Grade AI Interview Coach API Backend",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(questions_router)
app.include_router(interview_router)
app.include_router(ws_router)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.PROJECT_NAME} backend server...")
    await connect_to_mongo()
    
    # Startup validation for Gemini API configuration
    if settings.is_gemini_configured():
        logger.info(f"Gemini Suggestion Service: Configured with model '{settings.GEMINI_MODEL}' (API key detected)")
    else:
        logger.warning("Gemini Suggestion Service: GEMINI_API_KEY is not configured or empty. AI Suggestions will operate in deterministic fallback mode.")

    # Start background cleanup worker for temporary video files
    asyncio.create_task(CleanupService.start_background_cleanup_worker(interval_minutes=15))

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down backend server...")
    await close_mongo_connection()

@app.get("/")
async def root_health_check():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "whisper_model": settings.WHISPER_MODEL,
        "compute_type": settings.WHISPER_COMPUTE_TYPE,
        "gemini_model": settings.GEMINI_MODEL
    }
