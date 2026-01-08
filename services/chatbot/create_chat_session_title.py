from models.LLM import load_llm
from langchain_core.messages import SystemMessage, HumanMessage


def generate_llm_chat_title(query: str) -> str:
    """
    Generate a short chat title (3–6 words) using LLM.
    Deterministic, cheap, safe.
    """

    llm = load_llm()

    system_prompt = SystemMessage(
        content=(
            "You generate short chat titles.\n"
            "Rules:\n"
            "- 3 to 6 words\n"
            "- No punctuation\n"
            "- No emojis\n"
            "- Title case\n"
            "- No explanations\n"
            "- No religious preaching\n"
            "- Output ONLY the title"
        )
    )

    human_prompt = HumanMessage(content=query)

    try:
        result = llm.invoke([system_prompt, human_prompt],max_tokens=20)
        title = result.content.strip()
        return title[:255] or "New Chat"
    except Exception:
        return "New Chat"
