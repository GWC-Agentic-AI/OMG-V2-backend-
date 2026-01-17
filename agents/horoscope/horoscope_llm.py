import json
import re
from langchain_core.messages import HumanMessage
from tools.tavily_search import web_search_tool
from models.LLM import load_llm

llm = load_llm()

def safe_json_parse(text: str) -> dict:
    if not text:
        raise ValueError("Empty LLM response")

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found: {text}")

    return json.loads(match.group())


def generate_one_rasi(rasi: str) -> dict:
    search_data = web_search_tool.invoke(
        f"{rasi} daily horoscope today astrology"
    ) or "General astrology guidance"

    prompt = f"""
You are an expert astrologer.

Based on the information below:
{search_data}

Generate today's horoscope for {rasi}.

Return STRICT JSON ONLY:

{{
  "health": "...",
  "career": "...",
  "love": "...",
  "wealth": "...",
  "travel": "...",
  "summary": "...",
  "ratings": {{
    "health": 1-5,
    "career": 1-5,
    "love": 1-5,
    "wealth": 1-5,
    "travel": 1-5
  }}
}}
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return safe_json_parse(response.content)



def translate_horoscope(data: dict, target_lang: str) -> dict:
    prompt = f"""
Translate the following horoscope to language code "{target_lang}".
Preserve meaning.
Return STRICT JSON with same keys.

Input:
{json.dumps(data, ensure_ascii=False)}
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return safe_json_parse(response.content)
