from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role types"""
    USER = "user"
    ASSISTANT = "assistant"


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., min_length=1, max_length=2000, description="User's question")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123",
                "session_id": "session_abc",
                "query": "I feel lost in my career path"
            }
        }
    )


class ChatMessage(BaseModel):
    """Individual chat message"""
    id: Optional[int] = None
    role: MessageRole
    content: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    success: bool = True
    guidance: str
    session_id: str
    message_id: Optional[int] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "guidance": "कर्मण्येवाधिकारस्ते...",
                "session_id": "session_abc",
                "message_id": 42
            }
        }
    )


class SessionSummary(BaseModel):
    """Summary of a chat session"""
    session_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(default=30, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate SQL offset"""
        return (self.page - 1) * self.limit


class PaginatedMessages(BaseModel):
    """Paginated chat history response"""
    messages: List[ChatMessage]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [],
                "total_count": 150,
                "page": 1,
                "limit": 30,
                "total_pages": 5,
                "has_next": True,
                "has_previous": False
            }
        }
    )


class SessionListResponse(BaseModel):
    """Response for listing sessions"""
    sessions: List[SessionSummary]
    total_count: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sessions": [],
                "total_count": 10
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "Invalid request",
                "detail": "Query cannot be empty"
            }
        }
    )