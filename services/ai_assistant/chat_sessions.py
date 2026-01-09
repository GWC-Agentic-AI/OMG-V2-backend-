from db.session import get_db
from config import settings

APP_DB_NAME = settings.AI_DB


def session_exists(user_id: str, session_id: str) -> bool:
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM chatbot_chat_sessions
                WHERE user_id=%s AND session_id=%s
                """,
                (user_id, session_id),
            )
            return cur.fetchone() is not None


def create_chat_session(user_id: str, session_id: str, title: str):
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chatbot_chat_sessions (user_id, session_id, title)
                VALUES (%s, %s, %s)
                ON CONFLICT (session_id) DO NOTHING
                """,
                (user_id, session_id, title),
            )


def fetch_user_chat_sessions(user_id: str):
    """
    Fetch all chat sessions for a user ordered by latest activity.
    """

    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    session_id,
                    title,
                    created_at
                FROM chatbot_chat_sessions
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()

    return [
        {
            "sessionId": session_id,
            "sessionTitle": title,
            "created_at": created_at,
        }
        for session_id, title, created_at in rows
    ]
    