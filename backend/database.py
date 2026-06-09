from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

_pool: ThreadedConnectionPool | None = None


def _get_pool() -> ThreadedConnectionPool:
    """Lazily create a process-wide connection pool.

    Building the pool on first use (rather than at import) keeps imports cheap
    and avoids needing DATABASE_URL until a request actually hits the database.
    """
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL,
            cursor_factory=RealDictCursor,
        )
    return _pool


@contextmanager
def get_cursor(commit: bool = False):
    """Borrow a pooled connection and yield a cursor.

    Commits on clean exit when ``commit`` is True; always rolls back on error
    and returns the connection to the pool.
    """
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def init_db() -> None:
    with get_cursor(commit=True) as c:
        c.execute('''
            CREATE TABLE IF NOT EXISTS bottles (
                id SERIAL PRIMARY KEY,
                winery TEXT,
                wine_name TEXT,
                region TEXT,
                appellation TEXT,
                varietal TEXT,
                vintage INTEGER,
                quantity INTEGER,
                drink_from INTEGER,
                drink_by INTEGER,
                your_notes TEXT,
                your_rating REAL,
                expert_notes TEXT,
                user_id TEXT,
                purchase_price REAL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS consumption_log (
                id SERIAL PRIMARY KEY,
                bottle_id INTEGER,
                winery TEXT,
                wine_name TEXT,
                vintage INTEGER,
                varietal TEXT,
                region TEXT,
                quantity INTEGER DEFAULT 1,
                consumed_on DATE,
                notes TEXT,
                user_id TEXT
            )
        ''')
        # Migrations (idempotent)
        c.execute('ALTER TABLE bottles ADD COLUMN IF NOT EXISTS user_id TEXT')
        c.execute('ALTER TABLE bottles ADD COLUMN IF NOT EXISTS purchase_price REAL')
        # Indexes — every query filters by user_id, so index it on both tables.
        c.execute('CREATE INDEX IF NOT EXISTS idx_bottles_user_id ON bottles (user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_log_user_id ON consumption_log (user_id)')


def add_bottle(winery, wine_name, region, appellation, varietal, vintage, quantity,
               drink_from, drink_by, your_notes, your_rating, expert_notes, user_id=None,
               purchase_price=None) -> None:
    with get_cursor(commit=True) as c:
        c.execute('''
            INSERT INTO bottles (winery, wine_name, region, appellation, varietal, vintage,
                                 quantity, drink_from, drink_by, your_notes, your_rating,
                                 expert_notes, user_id, purchase_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (winery, wine_name, region, appellation, varietal, vintage, quantity,
              drink_from, drink_by, your_notes, your_rating, expert_notes, user_id, purchase_price))


def get_bottles(user_id: str | None = None) -> list[dict[str, Any]]:
    with get_cursor() as c:
        if user_id:
            c.execute("SELECT * FROM bottles WHERE user_id = %s ORDER BY id", (user_id,))
        else:
            c.execute("SELECT * FROM bottles ORDER BY id")
        return [dict(row) for row in c.fetchall()]


def get_bottle(bottle_id: int, user_id: str | None = None) -> dict[str, Any] | None:
    with get_cursor() as c:
        if user_id:
            c.execute(
                "SELECT * FROM bottles WHERE id = %s AND (user_id = %s OR user_id IS NULL)",
                (bottle_id, user_id),
            )
        else:
            c.execute("SELECT * FROM bottles WHERE id = %s", (bottle_id,))
        row = c.fetchone()
        return dict(row) if row else None


def update_bottle(id, winery, wine_name, region, appellation, varietal, vintage,
                  quantity, drink_from, drink_by, your_notes, your_rating,
                  expert_notes, user_id=None, purchase_price=None) -> None:
    with get_cursor(commit=True) as c:
        c.execute('''
            UPDATE bottles SET
                winery=%s, wine_name=%s, region=%s, appellation=%s, varietal=%s, vintage=%s,
                quantity=%s, drink_from=%s, drink_by=%s, your_notes=%s,
                your_rating=%s, expert_notes=%s, purchase_price=%s
            WHERE id=%s AND (user_id=%s OR user_id IS NULL)
        ''', (winery, wine_name, region, appellation, varietal, vintage, quantity,
              drink_from, drink_by, your_notes, your_rating, expert_notes, purchase_price, id, user_id))


def delete_bottle(id, user_id=None) -> None:
    with get_cursor(commit=True) as c:
        c.execute(
            "DELETE FROM bottles WHERE id=%s AND (user_id=%s OR user_id IS NULL)",
            (id, user_id),
        )


def log_consumption(bottle_id, winery, wine_name, vintage, varietal, region,
                    quantity, consumed_on, notes, user_id=None) -> None:
    with get_cursor(commit=True) as c:
        c.execute('''
            INSERT INTO consumption_log
                (bottle_id, winery, wine_name, vintage, varietal, region,
                 quantity, consumed_on, notes, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (bottle_id, winery, wine_name, vintage, varietal, region,
              quantity, consumed_on, notes, user_id))


def get_consumption_log(user_id: str | None = None) -> list[dict[str, Any]]:
    with get_cursor() as c:
        if user_id:
            c.execute(
                "SELECT * FROM consumption_log WHERE user_id = %s "
                "ORDER BY consumed_on DESC, id DESC",
                (user_id,),
            )
        else:
            c.execute("SELECT * FROM consumption_log ORDER BY consumed_on DESC, id DESC")
        return [dict(row) for row in c.fetchall()]
