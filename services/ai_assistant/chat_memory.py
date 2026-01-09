from langchain_core.messages import HumanMessage, AIMessage

from db.session import get_db
from config import settings

MAX_CONTEXT_MESSAGES = 12
APP_DB_NAME = settings.AI_DB


def save_messages_atomic(
    user_id: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
):
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chatbot_chat_messages (user_id, session_id, role, content)
                VALUES
                    (%s, %s, 'user', %s),
                    (%s, %s, 'assistant', %s)
                """,
                (
                    user_id, session_id, user_message,
                    user_id, session_id, assistant_message,
                ),
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
    
def fetch_conversation_paginated(
    user_id: str,
    session_id: str,
    limit: int,
    offset: int,
):
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM chatbot_chat_messages
                WHERE user_id=%s AND session_id=%s
                """,
                (user_id, session_id),
            )
            total = cur.fetchone()[0]

            cur.execute(
                """
                SELECT role, content, created_at
                FROM chatbot_chat_messages
                WHERE user_id=%s AND session_id=%s
                ORDER BY created_at ASC
                LIMIT %s OFFSET %s
                """,
                (user_id, session_id, limit, offset),
            )
            rows = cur.fetchall()

    messages = [
        {
            "role": role,
            "content": content,
            "timestamp": created_at.isoformat(),
        }
        for role, content, created_at in rows
    ]

    return total, messages



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
