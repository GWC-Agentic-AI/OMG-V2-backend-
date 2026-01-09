from services.ai_assistant.chat_sessions import session_exists, create_chat_session
from services.ai_assistant.chat_memory import (
    save_messages_atomic,
    fetch_context_messages,
)
from services.ai_assistant.llm_executor import run_agent, LLMExecutionError
from services.ai_assistant.create_chat_session_title import generate_llm_chat_title


async def handle_chat(
    user_id: str,
    session_id: str,
    query: str,
    vishnu_persona: bool,
):
    if not session_exists(user_id, session_id):
        title = generate_llm_chat_title(query)
        create_chat_session(user_id, session_id, title)

    context = fetch_context_messages(user_id, session_id)

    try:
        answer = await run_agent(
            context_messages=context,
            user_query=query,
            session_id=session_id,
            vishnu_persona=vishnu_persona,
        )

        save_messages_atomic(
            user_id=user_id,
            session_id=session_id,
            user_message=query,
            assistant_message=answer,
        )

        return {
            "answer": answer,
            "success": True,
            "error_code": None,
        }

    except LLMExecutionError:
        print("LLM EXE",LLMExecutionError)
        return {
            "answer": None,
            "success": False,
            "error_code": "AGENT_FAILURE",
        }
