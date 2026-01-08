import psycopg2
from psycopg2.pool import SimpleConnectionPool
from config import settings

_POOLS = {}

def get_pool(db_name: str) -> SimpleConnectionPool:
    if db_name not in _POOLS:
        _POOLS[db_name] = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=db_name,
        )
    return _POOLS[db_name]
