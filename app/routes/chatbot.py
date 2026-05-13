from fastapi import HTTPException
from app.model import ChatMessage, ChatResponse
from app.prompts import CHATBOT_PROMPT
from app.utils import resolve_model
import google.generativeai as genai
import asyncio
import logging

logger = logging.getLogger(__name__)

async def draft_message(req: ChatMessage, gemini_model: str) -> dict:
    """Process RM query and draft professional client message."""
    try:
        logger.info(f"Processing draft request for RM: {req.rm_id}, Client: {req.client_id}")
        
        # Build comprehensive prompt
        context_section = f"\nAdditional Context:\n{req.context}" if req.context else ""
        
        # Build personalization section
        personalization = ""
        if req.client_name or req.rm_name:
            personalization = "\nPersonalization Details:\n"
            if req.client_name:
                personalization += f"- Client Name: {req.client_name}\n"
            if req.rm_name:
                personalization += f"- RM Name: {req.rm_name}\n"
        
        prompt = (
            f"{CHATBOT_PROMPT}\n"
            f"RM Request: {req.query}"
            f"{context_section}"
            f"{personalization}\n"
            f"Please draft a professional, ready-to-send message for the client.\n"
            f"{'Use the actual names provided above instead of placeholders.' if personalization else 'Use [Client Name] and [Your Name] as placeholders if names are not provided.'}\n"
            f"Output only the drafted message, no explanations."
        )
        
        model = genai.GenerativeModel(resolve_model(gemini_model))
        response = await asyncio.to_thread(model.generate_content, prompt)
        drafted_message = (response.text or "").strip()
        
        if not drafted_message:
            raise HTTPException(status_code=502, detail="Empty response from model")
        
        logger.info(f"Successfully drafted message for RM: {req.rm_id}")
        return {
            "rm_id": req.rm_id,
            "client_id": req.client_id,
            "query": req.query,
            "drafted_message": drafted_message
        }
    except Exception as e:
        logger.error(f"Error drafting message: {e}")
        raise HTTPException(status_code=500, detail=str(e))