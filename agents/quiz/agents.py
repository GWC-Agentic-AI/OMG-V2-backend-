import json
from langchain_openai import ChatOpenAI

TOPICS = [
    "Diwali festival",
    "Lord Shiva",
    "Lord Vishnu",
    "Lord Krishna stories",
    "Ramayana epic",
    "Mahabharata epic",
    "Hindu new moon (Amavasya)",
    "Hindu spirituality and philosophy"
]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

def quiz_generator_agent(state):
    num = state["num_questions"]

    prompt = f"""
Generate {num} MCQ questions in ENGLISH from Hindu topics.

Rules:
- 4 options
- correct_option_index 0-3
- JSON only

Format:
[
  {{
    "question": "...",
    "options": ["A","B","C","D"],
    "correct_option_index": 2
  }}
]
Topics: {TOPICS}
"""

    response = llm.invoke(prompt)
    questions = json.loads(response.content)

    return {"questions": questions}
