"""
memory/db.py — NayePankh AI Workforce
=======================================
Thread-safe SQLite connection manager.
- Initializes all 12 tables on first boot from db_schema.sql
- Provides helper functions used by tools/db_tools.py
"""
import sqlite3
import threading
import logging
from pathlib import Path
from typing import Any

# Resolve paths without importing config to avoid circular deps
_HERE       = Path(__file__).parent
_DB_PATH    = (_HERE / "nayepankh.db").resolve()
_SCHEMA     = _HERE.parent / "schemas" / "db_schema.sql"

logger = logging.getLogger(__name__)

# One connection per thread (Streamlit is multi-threaded)
_local = threading.local()


def get_connection(db_path: Path = _DB_PATH) -> sqlite3.Connection:
    """Return thread-local SQLite connection, creating tables if needed."""
    if not hasattr(_local, "conn") or _local.conn is None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row          # dict-like rows
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
        logger.info(f"[DB] Connected to {db_path}")
    return _local.conn


def init_db(db_path: Path = _DB_PATH) -> None:
    """
    Execute db_schema.sql to create all tables if they don't exist.
    Safe to call on every startup (all statements are CREATE IF NOT EXISTS).
    """
    if not _SCHEMA.exists():
        raise FileNotFoundError(f"Schema file not found: {_SCHEMA}")

    ddl = _SCHEMA.read_text(encoding="utf-8")
    conn = get_connection(db_path)
    try:
        conn.executescript(ddl)
        conn.commit()
        logger.info("[DB] Schema initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"[DB] Schema init failed: {e}")
        raise


def execute_query(
    sql: str,
    params: tuple = (),
    db_path: Path = _DB_PATH,
    fetch: str = "all",       # "all" | "one" | "none"
) -> Any:
    """
    Execute a single SQL statement with optional params.

    Args:
        sql:      SQL string (use ? placeholders)
        params:   Tuple of bind parameters
        fetch:    "all" → list[dict], "one" → dict|None, "none" → rowcount
    Returns:
        Depends on `fetch` argument.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        if fetch == "all":
            return [dict(row) for row in cur.fetchall()]
        elif fetch == "one":
            row = cur.fetchone()
            return dict(row) if row else None
        else:
            return cur.rowcount
    except sqlite3.Error as e:
        logger.error(f"[DB] Query error: {e}\nSQL: {sql}\nParams: {params}")
        raise


def execute_many(sql: str, data: list[tuple], db_path: Path = _DB_PATH) -> int:
    """Batch insert/update. Returns number of affected rows."""
    conn = get_connection(db_path)
    try:
        cur = conn.executemany(sql, data)
        conn.commit()
        return cur.rowcount
    except sqlite3.Error as e:
        logger.error(f"[DB] Batch error: {e}")
        raise


def close_connection() -> None:
    """Explicitly close the thread-local connection."""
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
        _local.conn = None
        logger.info("[DB] Connection closed.")
