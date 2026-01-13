from typing_extensions import TypedDict
from typing import Annotated, List, Optional

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
from agents.itinerary.itinerary_agent import _itinerary_logic
from services.itinerary.intent import is_itinerary_intent
from utils.logger import get_logger
import logging

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
    intent: str

    trip_days: Optional[int]
    itinerary_query: Optional[str]

    itinerary_in_progress: bool = None
    itinerary_completed: bool = None

def intent_router_node(state: State):
    last_user_msg = None
    for msg in reversed(state["messages"]):
        if msg.type == "human":
            last_user_msg = msg.content
            break
    print("[INFO] last user message",last_user_msg)

    if not last_user_msg:
        return {"intent": "general"}

    # print(f"[INFO] STATE - {state}")
    # CASE 1: Itinerary in progress → continue asking for days / generate
    if state.get("itinerary_in_progress"):
        print("[INFO] CASE 1 Executed")
        return {"intent": "itinerary"}

    # CASE 2: Itinerary completed → only allow NEW itinerary if user explicitly asks for a trip plan
    if state.get("itinerary_completed"):
        print("[INFO] CASE 2 Executed")
        result = is_itinerary_intent(llm, last_user_msg)
        if result["is_itinerary"] and result["trip_days"]:
            # New itinerary request with trip_days → start fresh
            return {
                "intent": "itinerary",
                "trip_days": result["trip_days"],
                "itinerary_query": last_user_msg,
                "itinerary_in_progress": True,
                "itinerary_completed": False,
            }
        # Any other question → general chat
        state["itinerary_in_progress"] = False
        return {"intent": "general"}
 

    # CASE 3: Fresh intent detection
    result = is_itinerary_intent(llm, last_user_msg)
    if result["is_itinerary"]:
        print("[INFO] CASE 3 Executed")
        return {
            "intent": "itinerary",
            "trip_days": result["trip_days"],
            "itinerary_query": last_user_msg,
            "itinerary_in_progress": True,
            "itinerary_completed": False,
        }

    # CASE 4: General question
    return {"intent": "general"}



def itinerary_node(state: State):
    response = _itinerary_logic(state)
    print("[INFO] RESPONSE MSG FROM NODE",response)
    return response


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

builder.add_node("intent_router", intent_router_node)
builder.add_node("itinerary", itinerary_node)
builder.add_node("router", router_node)
builder.add_node("tools", ToolNode(tools))
builder.add_node("validate", validator_node)
builder.add_node("fallback_router", fallback_router_node)
builder.add_node("final", final_node)

# builder.add_edge(START, "router")
builder.add_edge(START, "intent_router")

builder.add_conditional_edges(
    "intent_router",
    lambda s: s.get("intent", "general"),
    {
        "itinerary": "itinerary",
        "general": "router",
    }
)

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
