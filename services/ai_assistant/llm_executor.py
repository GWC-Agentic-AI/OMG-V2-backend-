import asyncio
from langchain_core.messages import HumanMessage
from app.ai_assistants.graph import graph

class LLMExecutionError(Exception):
    pass


async def run_agent(
    context_messages,
    user_query: str,
    session_id: str,
    vishnu_persona: bool,
) -> str:
    try:
        result = await asyncio.to_thread(
            graph.invoke,
            {
                "messages": context_messages + [HumanMessage(content=user_query)],
                "needs_fallback": False,
                "fallback_used": False,
                "vishnu_persona": vishnu_persona,
            },
            {"configurable": {"thread_id": session_id}},
        )

        messages = result.get("messages", [])
        if not messages:
            raise LLMExecutionError("Empty agent response")

        return messages[-1].content

    except Exception as e:
        print("EXCEPRTION",e)
        raise LLMExecutionError(str(e))
