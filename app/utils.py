import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)


def resolve_model(name: str) -> str:
    """Return a usable model id if available; log what is available otherwise."""
    try:
        available = [m.name for m in genai.list_models()
                     if "generateContent" in getattr(m, "supported_generation_methods", [])]
        short = [n.split("/")[-1] for n in available]
        if name in short:
            return name
        if name in available:
            return name.split("/")[-1]
        logger.warning(f"[Gemini] Requested model '{name}' not found. Available: {short}")
    except Exception as e:
        logger.error(f"[Gemini] Could not list models: {e}")
    return name