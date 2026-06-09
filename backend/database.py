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
    TCP keepalives reduce how often managed Postgres drops idle connections.
    """
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            dsn=DATABASE_URL,
            cursor_factory=RealDictCursor,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=3,
        )
    return _pool


def _checkout(pool: ThreadedConnectionPool):
    """Return a live pooled connection, recycling any the server has dropped.

    Managed Postgres and the network in between close idle connections, so a
    pooled handle can be dead by the time we reuse it. Ping each candidate with
    a trivial query and discard dead ones (``close=True``) rather than letting
    the request fail with a 500.
    """
    last_err: Exception | None = None
    for _ in range(pool.maxconn + 1):
        conn = pool.getconn()
        try:
            if conn.closed:
                raise psycopg2.OperationalError("connection already closed")
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            conn.rollback()
            return conn
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            last_err = e
            pool.putconn(conn, close=True)
    raise psycopg2.OperationalError("no live database connection available") from last_err


@contextmanager
def get_cursor(commit: bool = False):
    """Borrow a live pooled connection and yield a cursor.

    Commits on clean exit when ``commit`` is True (otherwise rolls back, so a
    read never leaves an idle-in-transaction connection in the pool). A
    connection that breaks mid-request is closed rather than returned, so the
    pool replaces it instead of handing the dead handle to the next caller.
    """
    pool = _get_pool()
    conn = _checkout(pool)
    try:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()
        else:
            conn.rollback()
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        pool.putconn(conn, close=True)
        raise
    except Exception:
        conn.rollback()
        pool.putconn(conn)
        raise
    else:
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
               drink_from, drink_by, your_notes, your_rating, expert_notes, user_id,
               purchase_price=None) -> None:
    with get_cursor(commit=True) as c:
        c.execute('''
            INSERT INTO bottles (winery, wine_name, region, appellation, varietal, vintage,
                                 quantity, drink_from, drink_by, your_notes, your_rating,
                                 expert_notes, user_id, purchase_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (winery, wine_name, region, appellation, varietal, vintage, quantity,
              drink_from, drink_by, your_notes, your_rating, expert_notes, user_id, purchase_price))


def get_bottles(user_id: str) -> list[dict[str, Any]]:
    with get_cursor() as c:
        c.execute("SELECT * FROM bottles WHERE user_id = %s ORDER BY id", (user_id,))
        return [dict(row) for row in c.fetchall()]


def get_bottle(bottle_id: int, user_id: str) -> dict[str, Any] | None:
    with get_cursor() as c:
        c.execute(
            "SELECT * FROM bottles WHERE id = %s AND user_id = %s",
            (bottle_id, user_id),
        )
        row = c.fetchone()
        return dict(row) if row else None


def update_bottle(id, winery, wine_name, region, appellation, varietal, vintage,
                  quantity, drink_from, drink_by, your_notes, your_rating,
                  expert_notes, user_id, purchase_price=None) -> None:
    with get_cursor(commit=True) as c:
        c.execute('''
            UPDATE bottles SET
                winery=%s, wine_name=%s, region=%s, appellation=%s, varietal=%s, vintage=%s,
                quantity=%s, drink_from=%s, drink_by=%s, your_notes=%s,
                your_rating=%s, expert_notes=%s, purchase_price=%s
            WHERE id=%s AND user_id=%s
        ''', (winery, wine_name, region, appellation, varietal, vintage, quantity,
              drink_from, drink_by, your_notes, your_rating, expert_notes, purchase_price, id, user_id))


def decrement_bottle(bottle_id: int, user_id: str, amount: int) -> int | None:
    """Atomically take ``amount`` bottles out of stock.

    Returns the remaining quantity, or None if the bottle doesn't exist (for
    this user) or doesn't have enough stock. The conditional UPDATE makes the
    check-and-decrement a single statement, so concurrent drinks can't both
    pass a read-then-write check and oversubtract.
    """
    with get_cursor(commit=True) as c:
        c.execute('''
            UPDATE bottles SET quantity = quantity - %s
            WHERE id = %s AND user_id = %s AND quantity >= %s
            RETURNING quantity
        ''', (amount, bottle_id, user_id, amount))
        row = c.fetchone()
        return row["quantity"] if row else None


def delete_bottle(id, user_id) -> None:
    with get_cursor(commit=True) as c:
        c.execute(
            "DELETE FROM bottles WHERE id=%s AND user_id=%s",
            (id, user_id),
        )


def log_consumption(bottle_id, winery, wine_name, vintage, varietal, region,
                    quantity, consumed_on, notes, user_id) -> None:
    with get_cursor(commit=True) as c:
        c.execute('''
            INSERT INTO consumption_log
                (bottle_id, winery, wine_name, vintage, varietal, region,
                 quantity, consumed_on, notes, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (bottle_id, winery, wine_name, vintage, varietal, region,
              quantity, consumed_on, notes, user_id))


def get_consumption_log(user_id: str) -> list[dict[str, Any]]:
    with get_cursor() as c:
        c.execute(
            "SELECT * FROM consumption_log WHERE user_id = %s "
            "ORDER BY consumed_on DESC, id DESC",
            (user_id,),
        )
        return [dict(row) for row in c.fetchall()]
