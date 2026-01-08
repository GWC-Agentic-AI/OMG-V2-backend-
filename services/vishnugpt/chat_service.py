from typing import List, Tuple
from datetime import datetime
import math
import asyncio

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from config import settings
from db.session import get_db
from schemas.vishnugpt.models import (
    ChatMessage,
    PaginatedMessages,
    SessionSummary,
    MessageRole,
)
from PROMPTS.vishnugpt.prompts import SYSTEM_PROMPT, TITLE_GENERATION_PROMPT
from utils.tokens import count_tokens
from services.vishnugpt.guardrails import guardrail_service
from models.LLM import load_llm


APP_DB_NAME = settings.AI_DB


class ChatService:
    """Service for handling chat operations"""

    def __init__(self):
        self.llm = load_llm()
        self.token_limit = settings.token_limit
        self.max_history = settings.max_history_messages

    def generate_session_title(self, first_message: str) -> str:
        """Generate a short spiritual title for new session"""
        try:
            messages = [
                SystemMessage(content=TITLE_GENERATION_PROMPT),
                HumanMessage(content=first_message),
            ]
            response = self.llm.invoke(messages)
            return response.content.strip().replace('"', '')[:100]
        except Exception:
            return "Divine Guidance Session"

    def _ensure_session_exists(
        self, user_id: str, session_id: str, first_query: str
    ) -> None:
        with get_db(APP_DB_NAME) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT session_id FROM vishnugpt_chat_sessions WHERE session_id = %s",
                    (session_id,),
                )

                if not cursor.fetchone():
                    title = self.generate_session_title(first_query)
                    cursor.execute(
                        """
                        INSERT INTO vishnugpt_chat_sessions
                        (session_id, user_id, title, created_at, updated_at)
                        VALUES (%s, %s, %s, NOW(), NOW())
                        """,
                        (session_id, user_id, title),
                    )

    def _build_conversation_history(
        self, session_id: str, current_query: str
    ) -> List:
        current_tokens = (
            count_tokens(SYSTEM_PROMPT) + count_tokens(current_query)
        )

        with get_db(APP_DB_NAME) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT role, content
                    FROM vishnugpt_chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (session_id, self.max_history),
                )
                db_history = cursor.fetchall()

        history = []
        for role, content in db_history:
            msg_tokens = count_tokens(content)
            if current_tokens + msg_tokens > self.token_limit:
                break

            if role == MessageRole.USER.value:
                history.insert(0, HumanMessage(content=content))
            else:
                history.insert(0, AIMessage(content=content))

            current_tokens += msg_tokens

        return history

    def _save_messages(
        self,
        user_id: str,
        session_id: str,
        user_query: str,
        ai_response: str,
    ) -> int:
        with get_db(APP_DB_NAME) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO vishnugpt_chat_messages
                    (user_id, session_id, role, content, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (user_id, session_id, MessageRole.USER.value, user_query),
                )

                cursor.execute(
                    """
                    INSERT INTO vishnugpt_chat_messages
                    (user_id, session_id, role, content, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING id
                    """,
                    (
                        user_id,
                        session_id,
                        MessageRole.ASSISTANT.value,
                        ai_response,
                    ),
                )

                message_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    UPDATE vishnugpt_chat_sessions
                    SET updated_at = NOW()
                    WHERE session_id = %s
                    """,
                    (session_id,),
                )

                return message_id

    def get_divine_guidance(
        self, user_id: str, session_id: str, user_query: str
    ) -> Tuple[str, int]:
        is_valid, _ = guardrail_service.validate_query(user_query)
        if not is_valid:
            return guardrail_service.get_rejection_message(), None

        self._ensure_session_exists(user_id, session_id, user_query)

        history = self._build_conversation_history(session_id, user_query)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *history,
            HumanMessage(content=user_query),
        ]

        # 🔑 LLM call OUTSIDE DB
        response = self.llm.invoke(messages)
        ai_response = response.content

        message_id = self._save_messages(
            user_id, session_id, user_query, ai_response
        )

        return ai_response, message_id

    def get_session_history(
        self, session_id: str, page: int = 1, limit: int = 30
    ) -> PaginatedMessages:
        offset = (page - 1) * limit

        with get_db(APP_DB_NAME) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM vishnugpt_chat_messages WHERE session_id = %s",
                    (session_id,),
                )
                total_count = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT id, role, content, created_at
                    FROM vishnugpt_chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at ASC
                    LIMIT %s OFFSET %s
                    """,
                    (session_id, limit, offset),
                )
                rows = cursor.fetchall()

        messages = [
            ChatMessage(
                id=r[0],
                role=MessageRole(r[1]),
                content=r[2],
                created_at=r[3],
            )
            for r in rows
        ]

        total_pages = max(math.ceil(total_count / limit), 1)

        return PaginatedMessages(
            messages=messages,
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

    def get_user_sessions(self, user_id: str) -> List[SessionSummary]:
        with get_db(APP_DB_NAME) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        cs.session_id,
                        cs.user_id,
                        cs.title,
                        cs.created_at,
                        cs.updated_at,
                        COUNT(cm.id)
                    FROM vishnugpt_chat_sessions cs
                    LEFT JOIN vishnugpt_chat_messages cm
                        ON cs.session_id = cm.session_id
                    WHERE cs.user_id = %s
                    GROUP BY
                        cs.session_id,
                        cs.user_id,
                        cs.title,
                        cs.created_at,
                        cs.updated_at
                    ORDER BY cs.updated_at DESC
                    """,
                    (user_id,),
                )
                rows = cursor.fetchall()

        return [
            SessionSummary(
                session_id=r[0],
                user_id=r[1],
                title=r[2],
                created_at=r[3],
                updated_at=r[4],
                message_count=r[5],
            )
            for r in rows
        ]
