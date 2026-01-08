from langchain_core.messages import HumanMessage, AIMessage

from db.session import get_db
from config import settings

MAX_CONTEXT_MESSAGES = 12
APP_DB_NAME = settings.AI_DB


def save_message(user_id: str, session_id: str, role: str, content: str):
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chatbot_chat_messages
                (user_id, session_id, role, content)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, session_id, role, content),
            )


def fetch_full_conversation(user_id: str, session_id: str):
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT role, content, created_at
                FROM chatbot_chat_messages
                WHERE user_id=%s AND session_id=%s
                ORDER BY created_at ASC
                """,
                (user_id, session_id),
            )
            rows = cur.fetchall()

    return [
        {
            "role": role,
            "content": content,
            "timestamp": created_at.isoformat(),
        }
        for role, content, created_at in rows
    ]


def fetch_context_messages(user_id: str, session_id: str):
    """
    Only last N messages for LLM context (token-safe)
    """
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT role, content
                FROM chatbot_chat_messages
                WHERE user_id=%s AND session_id=%s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, session_id, MAX_CONTEXT_MESSAGES),
            )
            rows = cur.fetchall()

    messages = []
    for role, content in reversed(rows):
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))

    return messages
