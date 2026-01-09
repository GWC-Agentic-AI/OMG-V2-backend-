from fastapi import APIRouter
from schemas.ai_assistant.chat_models import ChatRequest, ChatResponse, ChatMeta
from services.ai_assistant.chat_orchestrator import handle_chat
from datetime import datetime
import re

router = APIRouter()

INJECTION_PATTERNS = [
    r"ignore .* instruction",
    r"system prompt",
    r"act as",
    r"call .* tool",
    r"developer message",
]

def is_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in INJECTION_PATTERNS)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):

    if is_prompt_injection(req.query):
        return ChatResponse(
            answer="I can assist only with spiritual and temple-related queries.",
            meta=ChatMeta(
                session_id=req.session_id,
                success=True,
                timestamp=datetime.utcnow(),
            ),
        )

    result = await handle_chat(
        user_id=req.user_id,
        session_id=req.session_id,
        query=req.query,
        vishnu_persona=req.vishnuPersona,
    )

    return ChatResponse(
        answer=result["answer"],
        meta=ChatMeta(
            session_id=req.session_id,
            success=result["success"],
            error_code=result["error_code"],
            timestamp=datetime.utcnow(),
        ),
    )
