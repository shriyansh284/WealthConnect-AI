from fastapi import HTTPException
from app.model import HealthResponse, DetailedHealthResponse
import google.generativeai as genai
from app.utils import resolve_model
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_health_check(gemini_model: str) -> dict:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "gemini_model": gemini_model
    }

async def get_detailed_health_check(gemini_model: str, gemini_api_key: str) -> dict:
    """Detailed health check with model availability."""
    try:
        available_models = [m.name for m in genai.list_models()
                           if "generateContent" in getattr(m, "supported_generation_methods", [])]
        return {
            "status": "healthy",
            "version": "1.0.0",
            "gemini_model": gemini_model,
            "gemini_api_configured": bool(gemini_api_key),
            "available_models": available_models[:5]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

async def get_readiness_check(gemini_model: str) -> dict:
    """Readiness check - ensures service is ready to accept requests."""
    try:
        model = genai.GenerativeModel(resolve_model(gemini_model))
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")