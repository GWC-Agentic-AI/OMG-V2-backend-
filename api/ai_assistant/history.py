from fastapi import APIRouter, HTTPException, Query
from schemas.ai_assistant.chat_models import PaginatedConversationOut, PaginationMeta
from services.ai_assistant.chat_memory import fetch_conversation_paginated
from schemas.ai_assistant.session_models import ChatSessionListResponse
from services.ai_assistant.chat_sessions import fetch_user_chat_sessions

router = APIRouter()

@router.get(
    "/sessions/{session_id}/messages",
    response_model=PaginatedConversationOut,
)
def get_conversation(
    user_id: str,
    session_id: str,
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    total, messages = fetch_conversation_paginated(
        user_id=user_id,
        session_id=session_id,
        limit=limit, 
        offset=offset,
    )

    if total == 0:
        raise HTTPException(status_code=204, detail="Session not found")

    return {
        "user_id": user_id,
        "session_id": session_id,
        "pagination": PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
        ),
        "messages": messages,
    }


@router.get(
    "/sessions",
    response_model=ChatSessionListResponse,
)
def get_user_sessions(user_id: str):
    """
    Fetch all chat sessions for a user.
    """

    sessions = fetch_user_chat_sessions(user_id)

    if not sessions:
        return {
            "success": True,
            "message": "No sessions found",
            "chatMeta": [],
        }

    return {
        "success": True,
        "message": "Successful retrieve data",
        "chatMeta": sessions,
    }
