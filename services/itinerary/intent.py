import json
from typing import TypedDict, Optional
from langchain_core.messages import SystemMessage, HumanMessage


class ItineraryIntentResult(TypedDict):
    is_itinerary: bool
    trip_days: Optional[int]


def is_itinerary_intent(llm, user_text: str) -> ItineraryIntentResult:
    """
    Detects itinerary intent AND extracts number of days.
    Multilingual (English + Tamil + mixed).
    """

    if not user_text or not user_text.strip():
        return {
            "is_itinerary": False,
            "trip_days": None
        }

    system_prompt = (
        "You are an intent extraction engine.\n\n"
        "Your tasks:\n"
        "1. Decide if the user is asking for a TRAVEL ITINERARY.\n"
        "   - This includes planning, visiting, or trip-related requests.\n"
        "2. Extract the number of DAYS if explicitly mentioned.\n\n"

        "IMPORTANT RULES:\n"
        "- If the user mentions planning, visiting, or a trip to a place,\n"
        "  it IS an itinerary intent even if days are NOT mentioned.\n"
        "- If days are not mentioned, return null for trip_days.\n"
        "- Understand English, Tamil, and mixed language.\n"
        "- Respond ONLY in valid JSON. No explanation.\n\n"

        "Response format:\n"
        "{\n"
        '  "is_itinerary": true | false,\n'
        '  "trip_days": number | null\n'
        "}\n\n"

        "TRUE examples:\n"
        "- Plan 2 day trip to Tirupati\n"
        "- Tirupati itinerary\n"
        "- 3 நாள் திருப்பதி பயண திட்டம்\n"
        "- Tirupati trip plan for 2 days\n"
        "- I plan to visit Tirupati temple\n"
        "- I want to go to Tiruchendur temple\n\n"

        "FALSE examples:\n"
        "- About Tirupati temple\n"
        "- Darshan timings\n"
        "- History of temple\n"
        "- Temple architecture\n"
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_text),
    ])

    try:
        data = json.loads(response.content.strip())
        return {
            "is_itinerary": bool(data.get("is_itinerary")),
            "trip_days": data.get("trip_days"),
        }
    except Exception:
        # Fail safe
        return {
            "is_itinerary": False,
            "trip_days": None
        }
