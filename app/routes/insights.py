from fastapi import HTTPException
from app.model import InsightRequest, ApprovalRequest
from app.prompts import STATIC_EDIT_PROMPT, REFINEMENT_PROMPT
from app.utils import resolve_model
import google.generativeai as genai
import asyncio
import logging

logger = logging.getLogger(__name__)

def build_personalization(rm_name: str = None, client_name: str = None) -> str:
    """Build personalization details string."""
    personalization = ""
    if rm_name or client_name:
        personalization = "Personalization Details:\n"
        if client_name:
            personalization += f"- Client Name: {client_name}\n"
        if rm_name:
            personalization += f"- RM/Sender Name: {rm_name}\n"
        personalization += "\n"
    return personalization

async def process_edit_insight(req: InsightRequest, gemini_model: str) -> dict:
    """
    Auto-generates first draft from raw insight.
    When RM clicks 'Edit', this endpoint automatically transforms the raw insight into an enhanced,
    formatted, client-ready message. No user query needed—just the raw insight.
    """
    try:
        logger.info(f"Auto-generating first draft for client: {req.client_id}")
        
        personalization = build_personalization(req.rm_name, req.client_name)
        client_greeting = req.client_name if req.client_name else "[Client Name]"
        rm_signature = req.rm_name if req.rm_name else "[Your Name]"
        
        prompt = STATIC_EDIT_PROMPT.format(
            insight=req.raw_insight,
            personalization=personalization,
            client_greeting=client_greeting,
            rm_signature=rm_signature
        )
        
        model = genai.GenerativeModel(resolve_model(gemini_model))
        response = await asyncio.to_thread(model.generate_content, prompt)
        edited = (response.text or "").strip()
        
        if not edited:
            raise HTTPException(status_code=502, detail="Empty response from model")
        
        logger.info(f"Successfully processed insight for client: {req.client_id}")
        return {
            "client_id": req.client_id,
            "edited_insight": edited,
            "rm_name": req.rm_name,
            "client_name": req.client_name
        }
    except Exception as e:
        logger.error(f"Error processing edit-insight: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_approval(req: ApprovalRequest, gemini_model: str) -> dict:
    """
    approve: returns final_message as-is.
    edit_again: applies rm_instruction to modify edited_insight (uses model).
    """
    try:
        logger.info(f"Processing {req.action} for client: {req.client_id}")
        
        if req.action == "approve":
            logger.info(f"Approved insight for client: {req.client_id}")
            return {
                "status": "approved",
                "client_id": req.client_id,
                "final_message": req.edited_insight,
                "rm_name": req.rm_name,
                "client_name": req.client_name
            }

        elif req.action == "edit_again":
            if not req.rm_instruction:
                raise HTTPException(status_code=400, detail="rm_instruction is required for edit_again")

            personalization = build_personalization(req.rm_name, req.client_name)
            client_greeting = req.client_name if req.client_name else "[Client Name]"
            rm_signature = req.rm_name if req.rm_name else "[Your Name]"
            
            prompt = REFINEMENT_PROMPT.format(
                instruction=req.rm_instruction,
                edited_insight=req.edited_insight,
                personalization=personalization,
                client_greeting=client_greeting,
                rm_signature=rm_signature
            )
            
            model = genai.GenerativeModel(resolve_model(gemini_model))
            response = await asyncio.to_thread(model.generate_content, prompt)
            edited_again = (response.text or "").strip()
            
            if not edited_again:
                raise HTTPException(status_code=502, detail="Empty response from model")
            
            logger.info(f"Re-edited insight for client: {req.client_id}")
            return {
                "client_id": req.client_id,
                "edited_insight": edited_again,
                "rm_name": req.rm_name,
                "client_name": req.client_name
            }

        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    except Exception as e:
        logger.error(f"Error processing insight: {e}")
        raise HTTPException(status_code=500, detail=str(e))