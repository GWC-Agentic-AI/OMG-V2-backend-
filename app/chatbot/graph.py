from typing_extensions import TypedDict
from typing import Annotated, List

from langchain_core.messages import (
    AnyMessage,
    SystemMessage,
    trim_messages,
)
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from models.LLM import load_llm
from tools.db_tool import temple_db_tool
from tools.tavily_search import web_search_tool
from PROMPTS.chatbot.prompts import ROUTER_SYSTEM_PROMPT, FINAL_SYSTEM_PROMPT
from utils.logger import get_logger


logger = get_logger("spiritual_graph")

ALLOWED_TOOLS = {"temple_db_tool", "web_search_tool"}

llm = load_llm()

tools = [
    temple_db_tool,
    web_search_tool,
]

router_llm = llm.bind_tools(tools)

MAX_TOKENS = 3000


class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    needs_fallback: bool
    fallback_used: bool


def router_node(state: State):
    messages = trim_messages(
        state["messages"],
        max_tokens=MAX_TOKENS,
        strategy="last",
        token_counter=llm.get_num_tokens_from_messages,
    )

    response = router_llm.invoke(
        [ROUTER_SYSTEM_PROMPT] + messages
    )

    logger.info("[ROUTER] Tool planning completed")
    

    if getattr(response, "tool_calls", None):
        for call in response.tool_calls:
            logger.info(
                "[TOOL PLANNED] name=%s | args=%s",
                call["name"],
                call["args"],
            )
    else:
        logger.info("[ROUTER] No tool planned")

    return {
        "messages": [response],
        "needs_fallback": False,
        "fallback_used": state.get("fallback_used", False),
    }


def validator_node(state: State):

    if state.get("fallback_used"):
        return {"needs_fallback": False}

    tool_messages = [
        m for m in state["messages"]
        if m.type == "tool"
    ]

    if not tool_messages:
        return {"needs_fallback": False}

    last_tool = tool_messages[-1]

    if not last_tool.content or "EMPTY" in last_tool.content.upper():
        logger.warning(
            "[VALIDATOR] Empty tool output detected - fallback required"
        )
        return {"needs_fallback": True}

    return {"needs_fallback": False}


def fallback_router_node(state: State):
    fallback_prompt = SystemMessage(
        content=(
            "The previous tool returned no usable data.\n"
            "You MUST now call web_search_tool.\n"
            "DO NOT explain.\n"
            "DO NOT answer.\n"
        )
    )

    response = router_llm.invoke(
        [fallback_prompt] + state["messages"]
    )

    logger.info("[FALLBACK ROUTER] Forced web search planning")

    return {
        "messages": [response],
        "needs_fallback": False,
        "fallback_used": True,
    }


def final_node(state: State):
    response = llm.invoke(
        [FINAL_SYSTEM_PROMPT] + state["messages"]
    )
    return {"messages": [response]}


builder = StateGraph(State)

builder.add_node("router", router_node)
builder.add_node("tools", ToolNode(tools))
builder.add_node("validate", validator_node)
builder.add_node("fallback_router", fallback_router_node)
builder.add_node("final", final_node)

builder.add_edge(START, "router")

builder.add_conditional_edges(
    "router",
    tools_condition
)

builder.add_edge("tools", "validate")

builder.add_conditional_edges(
    "validate",
    lambda s: "fallback" if s["needs_fallback"] else "final",
    {
        "fallback": "fallback_router",
        "final": "final",
    }
)

builder.add_edge("fallback_router", "tools")
builder.add_edge("final", END)


graph = builder.compile(checkpointer=MemorySaver())
