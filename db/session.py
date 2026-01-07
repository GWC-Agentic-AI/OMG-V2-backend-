from contextlib import contextmanager
from db.engines import get_pool

@contextmanager
def get_db(db_name: str):
    pool = get_pool(db_name)
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)
