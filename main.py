from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import uvicorn
import logging

from app.routes.chatbot import draft_message
from config import GEMINI_API_KEY, GEMINI_MODEL, CORS_ALLOW_ORIGINS
from app.model import HealthResponse, DetailedHealthResponse, InsightRequest, ApprovalRequest, ChatMessage, ChatResponse
from app.routes.health import get_health_check, get_detailed_health_check, get_readiness_check
from app.routes.insights import process_edit_insight, process_approval

# Configure logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="RM Insight Editor and Sender", version="1.0.0")

# CORS
allow_origins = ["*"] if CORS_ALLOW_ORIGINS == "*" else [o.strip() for o in CORS_ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

# Health Check Endpoints
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return await get_health_check(GEMINI_MODEL)

@app.get("/health/detailed", response_model=DetailedHealthResponse, tags=["Health"])
async def detailed_health_check():
    """Detailed health check with model availability."""
    return await get_detailed_health_check(GEMINI_MODEL, GEMINI_API_KEY)

@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - ensures service is ready to accept requests."""
    return await get_readiness_check(GEMINI_MODEL)

# API Endpoints
@app.post("/edit-insight", tags=["Insights"])
async def edit_insight(req: InsightRequest):
    """
    Auto-generates first draft from raw insight.
    When user clicks 'Edit', automatically transforms raw insight into enhanced client-ready message.
    No query required—only raw_insight is needed (plus optional client/RM names for personalization).
    """
    return await process_edit_insight(req, GEMINI_MODEL)
    

@app.post("/process-insight", tags=["Insights"])
async def process_insight(req: ApprovalRequest):
    """
    approve: returns final_message as-is.
    edit_again: applies rm_instruction to modify edited_insight (uses model).
    """
    return await process_approval(req, GEMINI_MODEL)

@app.post("/draft-message", response_model=ChatResponse, tags=["Message Drafting"])
async def draft_message_endpoint(req: ChatMessage):
    """Draft professional client messages based on RM requirements."""
    return await draft_message(req, GEMINI_MODEL)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)