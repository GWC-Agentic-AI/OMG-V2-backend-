from fastapi import Query,APIRouter,HTTPException
from schemas.quiz.quiz import GenerateQuizRequest
from datetime import date
from db.session import get_db
from config import settings

router = APIRouter()

APP_DB_NAME = settings.APP_DB

@router.get("/questions")
def get_all_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    try:
        offset = (page - 1) * page_size

        with get_db(APP_DB_NAME) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM gptquiz q
                    JOIN gptquiz_questions qq ON q.id = qq.quiz_id
                    """
                )
                total = cur.fetchone()[0]
                cur.execute(
                    """
                    SELECT
                        q.id AS quiz_id,
                        q.quiz_date,
                        qq.logical_question_id,
                        qq.lang_code,
                        qq.question,
                        qq.options,
                        qq.correct_option_index
                    FROM gptquiz q
                    JOIN gptquiz_questions qq ON q.id = qq.quiz_id
                    ORDER BY q.quiz_date DESC, qq.id
                    LIMIT %s OFFSET %s
                    """,
                    (page_size, offset),
                )

                rows = cur.fetchall()

        result = [
            {
                "quiz_id": row[0],
                "quiz_date": row[1],
                "logical_question_id": str(row[2]),
                "lang_code": row[3],
                "question": row[4],
                "options": row[5],
                "correct_option_index": row[6],
            }
            for row in rows
        ]

        return {
            
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
            "questions": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/questions/today")
def get_today_questions():
    try:
        with get_db(APP_DB_NAME) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        q.id AS quiz_id,
                        q.quiz_date,
                        qq.logical_question_id,
                        qq.lang_code,
                        qq.question,
                        qq.options,
                        qq.correct_option_index
                    FROM gptquiz q
                    JOIN gptquiz_questions qq ON q.id = qq.quiz_id
                    WHERE q.quiz_date = %s
                    ORDER BY qq.id
                    """,
                    (date.today(),),
                )

                rows = cur.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="No quiz found for today",
            )

        questions = []
        quiz_id = rows[0][0]

        for row in rows:
            questions.append(
                {
                    "logical_question_id": str(row[2]),
                    "lang_code": row[3],
                    "question": row[4],
                    "options": row[5],
                    "correct_option_index": row[6],
                }
            )

        return {
            "quiz_id": quiz_id,
            "quiz_date": date.today(),
            "count": len(questions),
            "questions": questions,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
