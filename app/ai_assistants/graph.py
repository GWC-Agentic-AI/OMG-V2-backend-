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
from PROMPTS.ai_assistant.prompts import (
    ROUTER_SYSTEM_PROMPT,
    FINAL_SYSTEM_PROMPT,
)
from PROMPTS.ai_assistant.vishnu_persona import VISHNU_PERSONA_PROMPT
from PROMPTS.ai_assistant.persona_reset import RESET_PERSONA_PROMPT
from PROMPTS.ai_assistant.router_vishnu import ROUTER_PROMPT_VISHNU
from utils.logger import get_logger


logger = get_logger("spiritual_graph")

llm = load_llm()

tools = [
    temple_db_tool,
    web_search_tool,
]

router_llm = llm.bind_tools(tools)

MAX_TOKENS = 3000


# =========================
# GRAPH STATE
# =========================
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    needs_fallback: bool
    fallback_used: bool
    vishnu_persona: bool


# =========================
# ROUTER NODE (NEVER ANSWERS)
# =========================
def router_node(state: State):
    messages = trim_messages(
        state["messages"],
        max_tokens=MAX_TOKENS,
        strategy="last",
        token_counter=llm.get_num_tokens_from_messages,
    )

    if state.get("vishnu_persona"):
        prompt = ROUTER_PROMPT_VISHNU
    else:
        prompt = ROUTER_SYSTEM_PROMPT

    response = router_llm.invoke(
        [prompt] + messages
    )
    
    logger.info("[ROUTER] Planning completed")

    return {
        "messages": [response],
        "needs_fallback": False,
        "fallback_used": state.get("fallback_used", False),
    }


# =========================
# VALIDATOR NODE
# =========================
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
        logger.warning("[VALIDATOR] Empty tool output")
        return {"needs_fallback": True}

    return {"needs_fallback": False}


# =========================
# FALLBACK ROUTER
# =========================
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

    logger.info("[FALLBACK ROUTER] Forced web search")

    return {
        "messages": [response],
        "needs_fallback": False,
        "fallback_used": True,
    }


# =========================
# FINAL NODE (ONLY ANSWERING STAGE)
# =========================
def final_node(state: State):
    messages = state["messages"]
    response = llm.invoke([FINAL_SYSTEM_PROMPT] + messages)
    return {"messages": [response]}


# =========================
# GRAPH BUILD
# =========================
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
