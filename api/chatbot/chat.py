from fastapi import APIRouter
from schemas.chatbot.chat_models import ChatRequest, ChatResponse
from app.chatbot.graph import graph
from services.chatbot.chat_memory import save_message, fetch_context_messages
from services.chatbot.chat_sessions import session_exists, create_chat_session
from services.chatbot.create_chat_session_title import generate_llm_chat_title
from langchain_core.messages import HumanMessage
import asyncio
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
            answer="I can assist only with spiritual and temple-related queries."
        )

    if not session_exists(req.user_id, req.session_id):
        title = generate_llm_chat_title(req.query)
        create_chat_session(req.user_id, req.session_id, title)

    save_message(req.user_id, req.session_id, "user", req.query)

    try:
        context_messages = fetch_context_messages(req.user_id, req.session_id)

        result = await asyncio.to_thread(
            graph.invoke,
            {
                "messages": context_messages + [HumanMessage(content=req.query)],
                "stage": None,
                "trip_days": None,
                "needs_fallback": False,
                "fallback_used": False,
            },
            {"configurable": {"thread_id": req.session_id}},
        )

        messages = result.get("messages", [])
        final_answer = messages[-1].content if messages else "No response"

    except Exception as e:
        # final_answer = (
        #     "Namaskaram. I am unable to respond at the moment due to a technical issue. "
        #     "Please try again shortly."
        # )

        final_answer = f"ERROR: {type(e).__name__} → {str(e)}"

    save_message(req.user_id, req.session_id, "assistant", final_answer)

    return ChatResponse(answer=final_answer)
