from datetime import date
from agents.horoscope.horoscope_llm import generate_one_rasi
from services.horoscope.horoscope_db import insert_horoscope, is_today_fully_generated
from constants.rasi import RASI_NAMES,RASIS,DEFAULT_LANG,SUPPORTED_RASI_LANGS


RASIS = list(RASI_NAMES["en"].keys())

def generate_daily_horoscope():
    today = date.today().isoformat()

    # Example check if already generated
    if is_today_fully_generated(today, DEFAULT_LANG):
        print("[INFO] Horoscope already generated")
        return {"status": "skipped", "message": "Horoscope already generated today"}

    print("[INFO] Generating English horoscope...")

    for rasi in RASIS:
        data = generate_one_rasi(rasi)
        insert_horoscope(rasi, today, DEFAULT_LANG, data)

    print("[INFO] Horoscope generation completed")
    return {"status": "completed", "message": "Horoscope generated successfully"}


def get_rasi_name(rasi_code: str, langcode: str) -> str:
    """
    Supported: hi, ta, kn, te
    Others → English
    """
    if langcode not in SUPPORTED_RASI_LANGS:
        langcode = "en"

    return RASI_NAMES.get(langcode, RASI_NAMES["en"]).get(
        rasi_code,
        rasi_code
    )