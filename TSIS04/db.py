# db.py — PostgreSQL integration via psycopg2

import datetime
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def _connect():
    """Return a new psycopg2 connection or raise RuntimeError."""
    if not PSYCOPG2_AVAILABLE:
        raise RuntimeError("psycopg2 is not installed. Run: pip install psycopg2-binary")
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def init_db():
    """Create the scores table if it doesn't exist. Returns (True, '') or (False, err_msg)."""
    try:
        conn = _connect()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id            SERIAL PRIMARY KEY,
                username      VARCHAR(64)  NOT NULL,
                score         INTEGER      NOT NULL,
                level_reached INTEGER      NOT NULL DEFAULT 1,
                timestamp     TIMESTAMP    NOT NULL DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        return True, ""
    except Exception as e:
        return False, str(e)


def save_score(username: str, score: int, level_reached: int):
    """Insert one row. Returns (True, '') or (False, err_msg)."""
    try:
        conn = _connect()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO scores (username, score, level_reached, timestamp) "
            "VALUES (%s, %s, %s, %s)",
            (username, score, level_reached, datetime.datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, ""
    except Exception as e:
        return False, str(e)


def get_top10():
    """
    Return list of dicts with keys: rank, username, score, level_reached, timestamp.
    Returns empty list on error.
    """
    try:
        conn = _connect()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT username, score, level_reached,
                   TO_CHAR(timestamp, 'YYYY-MM-DD') AS timestamp
            FROM scores
            ORDER BY score DESC
            LIMIT 10;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r, rank=i+1) for i, r in enumerate(rows)]
    except Exception:
        return []


def get_personal_best(username: str) -> int:
    """Return the highest score for *username*, or 0 if none / DB error."""
    try:
        conn = _connect()
        cur  = conn.cursor()
        cur.execute(
            "SELECT COALESCE(MAX(score), 0) FROM scores WHERE username = %s",
            (username,)
        )
        result = cur.fetchone()[0]
        cur.close()
        conn.close()
        return int(result)
    except Exception:
        return 0