import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST      = os.getenv("DB_HOST")
DB_PORT      = os.getenv("DB_PORT", "5432")
DB_NAME      = os.getenv("DB_NAME", "postgres")
DB_USER      = os.getenv("DB_USER", "postgres")
DB_PASSWORD  = os.getenv("DB_PASSWORD")

if not DATABASE_URL and (not DB_HOST or not DB_PASSWORD):
    raise RuntimeError(
        "No database credentials found. Set DATABASE_URL or DB_HOST + DB_PASSWORD in .env."
    )


def _parse_url(url):
    """Parse host/port/dbname/user from a postgres:// URL.
    Password is intentionally NOT taken from the URL to avoid percent-encoding issues.
    Use DB_PASSWORD env var instead.
    """
    from urllib.parse import urlparse, unquote
    r = urlparse(url)
    return {
        "host":   r.hostname,
        "port":   r.port or 5432,
        "dbname": r.path.lstrip("/") or "postgres",
        "user":   unquote(r.username) if r.username else "postgres",
    }


def get_connection():
    """Open a new database connection.
    Prefers DATABASE_URL for host/port/dbname/user.
    Always uses DB_PASSWORD env var for the password (avoids URL encoding issues).
    Falls back to individual DB_* vars if DATABASE_URL is not set.
    """
    if DATABASE_URL:
        kw = _parse_url(DATABASE_URL)
        # DB_PASSWORD overrides whatever is in the URL to avoid percent-encoding problems
        password = DB_PASSWORD or ""
        conn = psycopg2.connect(
            host=kw["host"],
            port=kw["port"],
            dbname=kw["dbname"],
            user=kw["user"],
            password=password,
            connect_timeout=10,
            sslmode="require",
        )
    else:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10,
            sslmode="require",
        )
    return conn


def test_connection():
    """Quick connectivity check. Returns (True, None) or (False, error_str)."""
    try:
        conn = get_connection()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def execute_query(sql, params=None, fetch=None):
    """
    Execute a SQL statement.
    fetch='all'  -> returns list of dicts
    fetch='one'  -> returns single dict
    fetch=None   -> commit only (INSERT/UPDATE/DELETE)
    Returns lastrowid for INSERT when fetch=None.
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                if fetch == "all":
                    return cur.fetchall()
                elif fetch == "one":
                    return cur.fetchone()
                else:
                    # For INSERT RETURNING or plain DML
                    try:
                        return cur.fetchone()
                    except Exception:
                        return None
    finally:
        conn.close()
