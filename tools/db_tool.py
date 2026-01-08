from langchain.tools import tool
from utils.logger import get_logger

from db.session import get_db
from config import settings

logger = get_logger("temple_db_tool")

TEMPLE_DB_NAME = settings.TEMPLE_DB


def resolve_temple_fuzzy(temple_name: str, limit: int = 2):
    """
    Resolve temple using fuzzy matching directly on temples table.
    No alias table is used.

    Runs STRICTLY on omg-temple-db
    """

    sql = """
    SELECT
        id,
        name,
        deity,
        city,
        state,
        timings,
        website,
        description,
        history,
        festivals,
        amenities,
        similarity(name, %(q)s) AS score
    FROM "Temples"
    WHERE similarity(name, %(q)s) > 0.3
    ORDER BY score DESC
    LIMIT %(limit)s;
    """

    with get_db(TEMPLE_DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                {
                    "q": temple_name,
                    "limit": limit,
                },
            )
            rows = cur.fetchall()

    return [
        {
            "temple_id": r[0],
            "name": r[1],
            "deity": r[2],
            "city": r[3],
            "state": r[4],
            "timings": r[5],
            "website": r[6],
            "description": r[7],
            "history": r[8],
            "festivals": r[9],
            "amenities": r[10],
            "confidence": r[11],
        }
        for r in rows
    ]


@tool
def temple_db_tool(temple_name: str):
    """Fetch verified temple details and timings from database."""
    logger.info(f"[EXEC] temple_db_tool | temple_name={temple_name}")

    result = resolve_temple_fuzzy(temple_name)

    if not result:
        logger.warning("[RESULT] temple_db_tool returned EMPTY")
    else:
        logger.info(f"[RESULT] temple_db_tool rows={len(result)}")

    return result
