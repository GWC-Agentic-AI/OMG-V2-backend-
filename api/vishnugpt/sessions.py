"""
app/api/v1/routes/sessions.py - Session management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
from langchain_openai import ChatOpenAI

from schemas.vishnugpt.models import SessionListResponse, ErrorResponse
from services.vishnugpt.chat_service import ChatService

router = APIRouter()


def get_chat_service() -> ChatService:
    return ChatService()


@router.get(
    "/user/{user_id}",
    response_model=SessionListResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Get all sessions for a user",
    description="Retrieve all chat sessions for a specific user"
)
async def get_user_sessions(user_id: str):
    """
    Get all sessions for a user
    
    - **user_id**: The user identifier
    
    Returns list of sessions ordered by most recent activity
    """
    try:
        chat_service = get_chat_service()
        
        sessions = chat_service.get_user_sessions(user_id)
        
        return SessionListResponse(
            sessions=sessions,
            total_count=len(sessions)
        )
    
    except Exception as e:
        print(f"Error in get_user_sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve sessions"
        )