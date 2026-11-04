"""
AI Tennis Assistant Endpoint
Context-aware, data-backed conversational agent.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.database.connection import get_db
from app.schemas.api_schemas import ChatQueryRequest, ChatQueryResponse
from app.services.ai_assistant import AITennisAssistant
from app.core.security import get_optional_user

router = APIRouter()

@router.post("/chat", response_model=ChatQueryResponse)
def chat_with_assistant(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """
    UNIQUE FEATURE 9 & 3: AI Tennis Analyst Chatbot.
    Runs strictly parameterized read-only queries against database records with zero hallucination.
    """
    user_id = current_user.user_id if current_user else None
    return AITennisAssistant.answer_query(db, request.prompt, user_id=user_id)
