from pydantic import BaseModel
from typing import Optional

class HealthResponse(BaseModel):
    status: str
    version: str
    gemini_model: str

class DetailedHealthResponse(HealthResponse):
    gemini_api_configured: bool
    available_models: list

class InsightRequest(BaseModel):
    client_id: str
    raw_insight: str
    rm_instruction: Optional[str] = None
    rm_name: Optional[str] = None  # RM/Sender name
    client_name: Optional[str] = None  # Client name

class ApprovalRequest(BaseModel):
    client_id: str
    edited_insight: str
    action: str
    rm_instruction: Optional[str] = None
    rm_name: Optional[str] = None  # RM/Sender name
    client_name: Optional[str] = None  # Client name

class ChatMessage(BaseModel):
    rm_id: str
    client_id: str
    query: str
    context: Optional[str] = None
    rm_name: Optional[str] = None
    client_name: Optional[str] = None

class ChatResponse(BaseModel):
    rm_id: str
    client_id: str
    query: str
    drafted_message: str