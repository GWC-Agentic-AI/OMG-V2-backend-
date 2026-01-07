from pydantic import BaseModel, Field
from typing import List

class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="Unique user id")
    session_id: str = Field(..., min_length=1, description="Chat session id")
    query: str = Field(..., min_length=1, max_length=500)

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Assistant reply")

class MessageOut(BaseModel):
    role: str
    content: str
    timestamp: str

class ConversationOut(BaseModel):
    user_id: str
    session_id: str
    messages: List[MessageOut]
