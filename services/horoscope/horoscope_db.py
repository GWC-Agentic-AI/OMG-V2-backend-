import json
from psycopg2.extras import RealDictCursor
from db.session import get_db
from config import settings
from constants.rasi import RASI_NAMES
from datetime import date

APP_DB_NAME = settings.AI_DB

def is_today_fully_generated(today: str, langcode: str) -> bool:
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM daily_horoscope
                WHERE horoscope_date = %s AND langcode = %s
                """,
                (today, langcode),
            )
            return cur.fetchone()[0] == 12



def is_translation_exists(rasi: str, today: str, langcode: str) -> bool:
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM daily_horoscope
                WHERE rasi=%s AND horoscope_date=%s AND langcode=%s
                """,
                (rasi, today, langcode)
            )
            return cur.fetchone() is not None

def fetch_today_english():
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM daily_horoscope
                WHERE horoscope_date = CURRENT_DATE
                  AND langcode = 'en'
                ORDER BY rasi
                """
            )
            return cur.fetchall()


def fetch_latest_english():
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM daily_horoscope
                WHERE langcode = 'en'
                ORDER BY horoscope_date DESC
                LIMIT 12
                """
            )
            return cur.fetchall()



def insert_horoscope(rasi: str, date_str: str, langcode: str, data: dict):
    """Insert a horoscope entry into the database."""
    # rasi_code = English key (like "Aries")
    rasi_code = RASI_NAMES["en"][rasi]

    # rasi_name = localized name based on langcode, fallback to English
    rasi_name = RASI_NAMES.get(langcode, {}).get(rasi, rasi_code)

    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO daily_horoscope (
                    rasi,
                    horoscope_date,
                    langcode,
                    health,
                    career,
                    love,
                    wealth,
                    travel,
                    summary,
                    ratings,
                    rasi_code,
                    rasi_name
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (rasi, horoscope_date, langcode) DO NOTHING
                """,
                (
                    rasi,
                    date_str,
                    langcode,
                    data["health"],
                    data["career"],
                    data["love"],
                    data["wealth"],
                    data["travel"],
                    data["summary"],
                    json.dumps(data["ratings"]),
                    rasi_code,
                    rasi_name
                )
            )
            conn.commit()


