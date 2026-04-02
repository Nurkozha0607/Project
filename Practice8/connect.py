import psycopg2
from config import DB_CONFIG


def get_connection():
    """Return a new psycopg2 connection using DB_CONFIG."""
    return psycopg2.connect(**DB_CONFIG)


def init_db(conn):
    """
    Create the phonebook table and the helper invalid-records table if they
    don't exist yet, then load functions.sql and procedures.sql so every
    function / procedure is always up-to-date.
    """
    sql_files = ["functions.sql", "procedures.sql"]

    with conn.cursor() as cur:
        # Core tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS phonebook (
                id    SERIAL PRIMARY KEY,
                name  VARCHAR(100) NOT NULL,
                phone VARCHAR(20)  NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS phonebook_invalid_records (
                name  TEXT,
                phone TEXT
            );
        """)

        # Load SQL definitions
        for filename in sql_files:
            try:
                with open(filename, "r", encoding="utf-8") as fh:
                    cur.execute(fh.read())
            except FileNotFoundError:
                print(f"[init_db] Warning: {filename} not found – skipping.")

    conn.commit()
    print("[init_db] Database initialised successfully.")