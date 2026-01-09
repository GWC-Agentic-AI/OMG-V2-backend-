from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1, max_length=500)
    vishnuPersona: bool = False


class ChatMeta(BaseModel):
    session_id: str
    success: bool
    error_code: Optional[str] = None
    timestamp: datetime


class ChatResponse(BaseModel):
    answer: Optional[str] = None
    meta: ChatMeta


class MessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: str


class ConversationOut(BaseModel):
    user_id: str
    session_id: str
    messages: List[MessageOut]


class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int


class PaginatedConversationOut(BaseModel):
    user_id: str
    session_id: str
    pagination: PaginationMeta
    messages: List[MessageOut]
