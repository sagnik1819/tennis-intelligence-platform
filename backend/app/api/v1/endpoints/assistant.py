"""
AI Tennis Assistant Endpoint
Context-aware, data-backed conversational agent with async background persistence.
"""
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Header
import jwt
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.core.security import ALGORITHM, SECRET_KEY
from app.database.connection import get_db_context
from app.models.entities import User
from app.schemas.api_schemas import ChatQueryRequest, ChatQueryResponse
from app.services.ai_assistant import AITennisAssistant

router = APIRouter()


def _resolve_user_id(authorization: Optional[str]) -> Optional[int]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        with get_db_context() as db:
            row = db.query(User.user_id).filter(User.email == email).first()
            return row[0] if row else None
    except Exception:
        return None


@router.post("/chat", response_model=ChatQueryResponse)
def chat_with_assistant(
    request: ChatQueryRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
):
    """
    UNIQUE FEATURE 9 & 3: AI Tennis Analyst Chatbot.
    Runs cached read-only queries against database records with zero hallucination.
    """
    user_id = _resolve_user_id(authorization)
    return AITennisAssistant.answer_query(
        None,
        request.prompt,
        user_id=user_id,
        background_tasks=background_tasks,
    )
