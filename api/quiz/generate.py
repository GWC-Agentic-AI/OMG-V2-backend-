from fastapi import APIRouter, HTTPException
from datetime import date
import json
import uuid
import asyncio

from schemas.quiz.quiz import GenerateQuizRequest
from app.quiz.graph import quiz_graph

from db.session import get_db
from config import settings

router = APIRouter()

APP_DB_NAME = settings.APP_DB


@router.post("/generate")
async def generate_quiz(req: GenerateQuizRequest):
    quiz_id = None
    questions = []

    try:
        with get_db(APP_DB_NAME) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO gptquiz
                    (quiz_date, num_of_questions, title, description, time_limit_seconds, difficulty)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (quiz_date) DO NOTHING
                    RETURNING id
                    """,
                    (
                        date.today(),
                        req.num_of_questions,
                        "Daily Quiz",
                        "Hindu Topics Quiz",
                        600,
                        "medium",
                    ),
                )

                row = cur.fetchone()
                if not row:
                    raise HTTPException(
                        status_code=400,
                        detail="Quiz already generated today",
                    )

                quiz_id = row[0]

        state = {
            "num_questions": req.num_of_questions,
            "questions": [],
        }

        result = await asyncio.to_thread(quiz_graph.invoke, state)
        questions = result["questions"]

        with get_db(APP_DB_NAME) as conn:
            with conn.cursor() as cur:
                for q in questions:
                    cur.execute(
                        """
                        INSERT INTO GPTquiz_questions
                        (quiz_id, logical_question_id, lang_code, question, options, correct_option_index)
                        VALUES (%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            quiz_id,
                            str(uuid.uuid4()),
                            "en",
                            q["question"],
                            json.dumps(q["options"]),
                            q["correct_option_index"],
                        ),
                    )

        return {
            "status": "success",
            "quiz_id": quiz_id,
            "questions": questions,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
