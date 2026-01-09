from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def load_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found")

    return ChatOpenAI(
        api_key=api_key,
        temperature=0.2,
        model="gpt-4.1"
    )
