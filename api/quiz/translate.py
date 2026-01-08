from fastapi import APIRouter, HTTPException
import json
import asyncio

from schemas.quiz.quiz import TranslateRequest
from langchain_openai import ChatOpenAI

from db.session import get_db
from config import settings

router = APIRouter()

translator = ChatOpenAI(model="gpt-4.1", temperature=0)

APP_DB_NAME = settings.APP_DB


@router.post("/translate")
async def translate_quiz(req: TranslateRequest):
    try:
        with get_db(APP_DB_NAME) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT logical_question_id, question, options, correct_option_index
                    FROM GPTquiz_questions
                    WHERE quiz_id=%s AND lang_code='en'
                    """,
                    (req.quiz_id,),
                )
                rows = cur.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="Quiz not found")

        translated_rows = []

        for logical_id, question, options, correct_idx in rows:
            prompt = f"""
            Translate the following multiple-choice question to '{req.lang_code}'.
            Do NOT change the order of options.
            Do NOT change the meaning of the correct answer.

            Question: {question}
            Options: {options}

            Return strictly JSON like this:
            {{
              "question": "...",
              "options": ["...", "...", "...", "..."]
            }}
            """

            res = await asyncio.to_thread(translator.invoke, prompt)
            raw = res.content.strip()

            if not raw:
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM returned empty output for question {logical_id}",
                )

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM returned invalid JSON for question {logical_id}: {raw}",
                )

            translated_rows.append(
                (
                    req.quiz_id,
                    logical_id,
                    req.lang_code,
                    data["question"],
                    json.dumps(data["options"], ensure_ascii=False),
                    correct_idx,
                )
            )
            
        with get_db(APP_DB_NAME) as conn:
            with conn.cursor() as cur:
                for row in translated_rows:
                    cur.execute(
                        """
                        INSERT INTO GPTquiz_questions
                        (quiz_id, logical_question_id, lang_code, question, options, correct_option_index)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        row,
                    )

        return {"status": "success", "translated_to": req.lang_code}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
