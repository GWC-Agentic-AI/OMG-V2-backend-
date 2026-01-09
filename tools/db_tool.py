from langchain.tools import tool
from utils.logger import get_logger

from db.session import get_db
from config import settings

logger = get_logger("temple_db_tool")

TEMPLE_DB_NAME = settings.TEMPLE_DB


def resolve_temple_fuzzy(temple_name: str, limit: int = 2):
    """
        Fetch verified Hindu temple details from the official temple database.

        PURPOSE:
        - Retrieve accurate, authoritative information about Hindu temples
        using fuzzy name matching.
        - Designed ONLY for Hindu temple-related queries.

        WHEN TO USE:
        - Temple name lookup
        - Temple history, deity, location
        - Darshan timings and special timings
        - Temple amenities, festivals, and description
        - Address and geographic details

        INPUT:
        - temple_name (str): Name of the temple provided by the user.
        Partial or approximate names are supported.

        OUTPUT:
        - A list of matching temples ordered by relevance (confidence score).
        - Each result may include:
            - temple_id
            - name
            - deity
            - city, state, address
            - timings and special_timings
            - history and description
            - festivals and amenities
            - website (if available)
            - latitude and longitude
            - confidence score (similarity match)

        IMPORTANT RULES:
        - This tool queries ONLY the verified internal temple database.
        - It MUST NOT be used for:
            - Festival dates
            - Muhurtham or calendar calculations
            - Non-temple or non-Hindu topics
        - If the result is EMPTY, the caller SHOULD:
            - Use a fallback search tool
            - Or ask the user for clarification

        DATA GUARANTEE:
        - All returned data is database-sourced.
        - No external knowledge or assumptions are used.
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
        similarity(name, %(q)s) AS score,
        address,
        lat,
        long,
        special_timings
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
            "address":r[12],
            "lat":r[13],
            "long":r[14],
            "special_timings":r[15]
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
