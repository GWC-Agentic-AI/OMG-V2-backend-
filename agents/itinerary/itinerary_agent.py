from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
import re
import logging
from models.LLM import load_llm
from tools.tavily_search import web_search_tool

llm = load_llm()


def _itinerary_logic(state):
    messages = state["messages"]
    trip_days = state.get("trip_days")

    itinerary_query = state.get("itinerary_query")
    if not itinerary_query:
        for m in reversed(messages):
            if isinstance(m, HumanMessage):
                itinerary_query = m.content
                state["itinerary_query"] = itinerary_query  # store original query
                break

    if trip_days is None:
        last_user_msg = state["messages"][-1].content if state["messages"] else ""
        match = re.search(r"\b(\d+)\b", last_user_msg)
        if match:
            trip_days = int(match.group())
            state["trip_days"] = trip_days

    if trip_days is None:
        clarify_prompt = SystemMessage(content=f"""
You are a spiritual travel assistant.

The user wants to plan a pilgrimage, but they have **not mentioned the number of days**.

Instructions:
1. Ask **only ONE clear follow-up question**: “How many days do you plan to travel?”.
2. Be polite, calm, and devotional.
3. **Respond strictly in the language used by the user**:
   - If the user wrote in Tamil → respond fully in Tamil.
   - If the user wrote in English → respond fully in English.
4. Do NOT generate the itinerary yet.
5. Do NOT explain anything else.


User request:
{itinerary_query}
""")
        response = llm.invoke([clarify_prompt])

        return {"messages": state["messages"] + [AIMessage(content=response.content)]}

    web_data = web_search_tool.invoke({
        "query": f"{itinerary_query} {trip_days} day devotional itinerary nearby temples"
    })

    prompt = SystemMessage(
        content=f"""
    You are an expert **Spiritual Travel Planner** specializing in Hindu pilgrimage journeys.

    Trip Duration: {trip_days} days

    Guidelines:

    1. Ask the user for the temple or location **ONLY if it is not already provided**. Otherwise, use the given location.
    2. Prioritize the **main temple mentioned by the user**.
    3. Include **nearby temples only if trip duration ≥ 2 days**.
    4. **Do not repeat any temple**.
    5. Maintain a **devotional, calm, and respectful tone** throughout.
    6. **Strictly use the language of the user**. 
    - If user asks in Tamil → respond fully in Tamil.
    - If user asks in English → respond fully in English.
    - Never mix languages.
    7. Include:
    - Ideal visit order
    - Suggested darshan time (morning / evening)
    - Approximate travel flow
    - Include what are the main things to visit in that temple like dont forget to visit this statue in that temple.
    8. Avoid:
    - Overloading with too many temples
    - Exact travel hours, prices, or unverifiable facts
    - Asking questions
    - Dont ask dates and all please make itinerary with the web_data and trip_data alone.

    Reference Information (strictly as guidance, do not hallucinate):
    {web_data}

    Output Requirements:

    - Respond **only in Markdown format** and only **User's language".
    - Start with a short **introductory blessing or devotional note**.
    - Provide **day-wise itinerary**:
        - **Day 1**: (temple visits + brief devotional description)
        - **Day 2**: ...
    - End with a **gentle spiritual closing message**.
    - Do NOT explain, comment, or ask questions.

    Give it in tamil if users asks in tamil

    Generate the **final itinerary only**.
    """
)
    response = llm.invoke([prompt])

    # state["itinerary_in_progress"] = False
    # state["itinerary_completed"] = True
    # state["trip_days"] = None
    # state["itinerary_query"] = None
    # state['messages'] = AIMessage(content=response.content)
    logging.info(f"Itinerary completed: {state.get('itinerary_completed')}")
    logging.info(f"Itinerary in progress: {state.get('itinerary_in_progress')}")
    print(f"Itinerary completed: {state.get('itinerary_completed')}")
    print(f"Itinerary in progress: {state.get('itinerary_in_progress')}")

    return {
    **state,
    "messages": state["messages"] + [AIMessage(content=response.content)],
    "itinerary_in_progress": False,
    "itinerary_completed": True,
    "trip_days": None,
    "itinerary_query": None,
}
    
itinerary_agent = RunnableLambda(_itinerary_logic)
