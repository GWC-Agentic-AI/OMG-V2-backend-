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

    # 1️⃣ Fetch today's English horoscope
    english_rows = fetch_today_english()

    # 2️⃣ Fallback to latest English horoscope
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

        # Optional: skip if already translated
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


@router.get("/today")
def get_today(langcode: str = "en"):
    today = date.today().isoformat()

    with get_db(APP_DB_NAME) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    rasi_code,
                    rasi_name,
                    health, career, love, wealth, travel, summary, ratings
                FROM daily_horoscope
                WHERE horoscope_date = %s AND langcode = %s
                ORDER BY rasi_code
                """,
                (today, langcode)
            )
            return cur.fetchall()



@router.get("/today/{rasi}")
def get_today_single(rasi: str, langcode: str = "en"):
    today = date.today().isoformat()

    with get_db(APP_DB_NAME) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM daily_horoscope
                WHERE rasi=%s AND horoscope_date=%s AND langcode=%s
                """,
                (rasi.title(), today, langcode)
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(404, "Horoscope not available")

    return row



