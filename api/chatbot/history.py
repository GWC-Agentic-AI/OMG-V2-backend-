from fastapi import APIRouter, HTTPException
from schemas.chatbot.chat_models import ConversationOut
from services.chatbot.chat_memory import fetch_full_conversation

router = APIRouter()

@router.get("/sessions/{session_id}/messages", response_model=ConversationOut)
def get_conversation(user_id: str, session_id: str):

    messages = fetch_full_conversation(user_id, session_id)

    if not messages:
        raise HTTPException(status_code=204, detail="Session not found")

    return {
        "user_id": user_id,
        "session_id": session_id,
        "messages": messages
    }
