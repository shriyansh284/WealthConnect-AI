# app/routes/__init__.py
from app.routes.health import get_health_check, get_detailed_health_check, get_readiness_check
from app.routes.insights import process_edit_insight, process_approval

__all__ = [
    "get_health_check",
    "get_detailed_health_check", 
    "get_readiness_check",
    "process_edit_insight",
    "process_approval",
]