from pydantic import BaseModel
from typing import List
from datetime import datetime


class ChatSessionMeta(BaseModel):
    sessionId: str
    sessionTitle: str
    created_at: datetime


class ChatSessionListResponse(BaseModel):
    success: bool
    message: str
    chatMeta: List[ChatSessionMeta]
