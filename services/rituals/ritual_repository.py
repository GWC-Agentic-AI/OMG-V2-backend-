import json
from psycopg2.extras import RealDictCursor
from db.session import get_db
from config import settings

APP_DB_NAME = settings.AI_DB


def fetch_cached_ritual(user_id: int, today_date: str):
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT calculated_raasi, ritual_json, parikaram 
                   FROM daily_rituals WHERE user_id = %s AND ritual_date = %s""",
                (user_id, today_date)
            )
            return cur.fetchone()


def save_new_ritual(user_id: int, date: str, lang: str, plan: dict):
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO daily_rituals 
                   (user_id, ritual_date, calculated_raasi, language, ritual_json, parikaram) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, date, plan['calculated_raasi'], lang, 
                 json.dumps(plan['rituals']), json.dumps(plan['parikaram']))
            )
        conn.commit()


def fetch_history(user_id: int, date: str):
    with get_db(APP_DB_NAME) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM daily_rituals WHERE user_id = %s AND ritual_date = %s",
                (user_id, date)
            )
            return cur.fetchone()
