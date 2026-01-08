from fastapi import APIRouter, HTTPException, Depends, status
from langchain_openai import ChatOpenAI

from schemas.vishnugpt.models import (
    ChatRequest, 
    ChatResponse, 
    ErrorResponse,
    PaginationParams,
    PaginatedMessages
)
from services.vishnugpt.chat_service import ChatService

router = APIRouter()


def get_chat_service() -> ChatService:
    return ChatService()


@router.post(
    "/message",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Send a message and get divine guidance",
    description="Send a query to Lord Vishnu and receive guidance from Bhagavad Gita"
)
async def send_message(request: ChatRequest):
    """
    Send a message and receive divine guidance
    
    - **user_id**: Unique identifier for the user
    - **session_id**: Session identifier for conversation continuity
    - **query**: The user's question or concern
    """
    try:
        chat_service = get_chat_service()
        
        guidance, message_id = chat_service.get_divine_guidance(
            user_id=request.user_id,
            session_id=request.session_id,
            user_query=request.query
        )
        
        return ChatResponse(
            success=True,
            guidance=guidance,
            session_id=request.session_id,
            message_id=message_id
        )
    
    except Exception as e:
        print(f"Error in send_message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A temporary cloud obscures the sun. Please try again."
        )


@router.get(
    "/history/{session_id}",
    response_model=PaginatedMessages,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    },
    summary="Get chat history with pagination",
    description="Retrieve paginated chat history for a specific session"
)
async def get_chat_history(
    session_id: str,
    page: int = 1,
    limit: int = 30
):
    """
    Get paginated chat history for a session
    
    - **session_id**: The session identifier
    - **page**: Page number (default: 1)
    - **limit**: Messages per page (default: 30, max: 100)
    """
    try:
        # Validate pagination params
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be >= 1"
            )
        
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
            
        chat_service = get_chat_service()
        
        history = chat_service.get_session_history(
            session_id=session_id,
            page=page,
            limit=limit
        )
        
        return history
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_chat_history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve chat history"
        )