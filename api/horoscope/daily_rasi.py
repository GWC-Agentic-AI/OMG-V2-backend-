from fastapi import APIRouter, HTTPException
from datetime import date
from psycopg2.extras import RealDictCursor

from db.session import get_db
from config import settings
from services.horoscope.horoscope_generator import generate_daily_horoscope,get_rasi_name
from services.horoscope.horoscope_db import (
    fetch_today_english,
    is_translation_exists,
    insert_horoscope,fetch_latest_english
)
from agents.horoscope.horoscope_llm import translate_horoscope

APP_DB_NAME = settings.AI_DB

router = APIRouter()

@router.post("/today/generate")
def generate_today_horoscope():
    """
    Generates today's horoscope in English (once per day).
    """
    result = generate_daily_horoscope()

    if result["status"] == "skipped":
        raise HTTPException(
            status_code=409,
            detail=result
        )

    return result

@router.get("/today/translate")
def translate_today(langcode: str):

    if not langcode or len(langcode) > 5:
        raise HTTPException(400, "Invalid language code")

    if langcode == "en":
        raise HTTPException(400, "English already exists")

    today = date.today()
    english_rows = fetch_today_english()
    if not english_rows:
        english_rows = fetch_latest_english()

    if not english_rows:
        raise HTTPException(404, "No English horoscope found")
    if len(english_rows) < 12:
        raise HTTPException(
            409,
            "English horoscope is not fully generated"
        )

    translated = 0

    for row in english_rows:
        rasi = row["rasi"]
        if is_translation_exists(rasi, today, langcode):
            continue

        translated_data = translate_horoscope(
            {
                "health": row["health"],
                "career": row["career"],
                "love": row["love"],
                "wealth": row["wealth"],
                "travel": row["travel"],
                "summary": row["summary"],
                "ratings": row["ratings"],
            },
            langcode
        )

        insert_horoscope(
            rasi,
            today,
            langcode,
            translated_data
        )

        translated += 1

    return {
        "date": today.isoformat(),
        "langcode": langcode,
        "translated": translated,
        "status": "completed"
    }


@router.get("/fetchallrasi")
def get_today(langcode: str = "en", date_user: str | None = None):
    horoscope_date = date_user or date.today().isoformat()

    with get_db(APP_DB_NAME) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            final_lang = langcode
            if langcode != "en":
                cur.execute(
                    """
                    SELECT 1
                    FROM daily_horoscope
                    WHERE horoscope_date = %s
                      AND langcode = %s
                    LIMIT 1
                    """,
                    (horoscope_date, langcode)
                )
                exists = cur.fetchone()

                if not exists:
                    final_lang = "en"  
            cur.execute(
                """
                SELECT
                    rasi_code,
                    rasi_name,
                    health,
                    career,
                    love,
                    wealth,
                    travel,
                    summary,
                    ratings,
                    langcode
                FROM daily_horoscope
                WHERE horoscope_date = %s
                  AND langcode = %s
                ORDER BY rasi_code
                """,
                (horoscope_date, final_lang)
            )

            data = cur.fetchall()

    return {
        "date": horoscope_date,
        "requested_lang": langcode,
        "served_lang": final_lang,
        "count": len(data),
        "data": data
    }





@router.get("/fetch")
def get_today_single(
    rasi: str,
    langcode: str = "en",
    date_user: str | None = None
):
    horoscope_date = date_user or date.today().isoformat()
    rasi_value = rasi.title()

    with get_db(APP_DB_NAME) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM daily_horoscope
                WHERE rasi = %s
                  AND horoscope_date = %s
                  AND langcode = %s
                """,
                (rasi_value, horoscope_date, langcode)
            )
            row = cur.fetchone()

            if not row and langcode != "en":
                cur.execute(
                    """
                    SELECT *
                    FROM daily_horoscope
                    WHERE rasi = %s
                      AND horoscope_date = %s
                      AND langcode = 'en'
                    """,
                    (rasi_value, horoscope_date)
                )
                row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Horoscope not available")

    return row