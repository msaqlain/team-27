from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.workflow_manager import workflow_manager
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Initialize workflow and supervisor on startup"""
    try:
        logger.info("Initializing workflow and supervisor...")
        await workflow_manager.initialize_services()
        logger.info("Workflow and supervisor initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing workflow: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Stopping workflow and supervisor...")
        workflow_manager.stop()
        logger.info("Workflow and supervisor stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping workflow: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Backend"} 