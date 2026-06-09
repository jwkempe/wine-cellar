from __future__ import annotations

import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import os

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_conn()
    c = conn.cursor()
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
    # Migrations
    c.execute('ALTER TABLE bottles ADD COLUMN IF NOT EXISTS user_id TEXT')
    c.execute('ALTER TABLE bottles ADD COLUMN IF NOT EXISTS purchase_price REAL')
    conn.commit()
    conn.close()


def add_bottle(winery, wine_name, region, appellation, varietal, vintage, quantity,
               drink_from, drink_by, your_notes, your_rating, expert_notes, user_id=None,
               purchase_price=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO bottles (winery, wine_name, region, appellation, varietal, vintage,
                             quantity, drink_from, drink_by, your_notes, your_rating,
                             expert_notes, user_id, purchase_price)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (winery, wine_name, region, appellation, varietal, vintage, quantity,
          drink_from, drink_by, your_notes, your_rating, expert_notes, user_id, purchase_price))
    conn.commit()
    conn.close()


def get_bottles(user_id: str | None = None) -> pd.DataFrame:
    conn = psycopg2.connect(DATABASE_URL)
    if user_id:
        df = pd.read_sql_query(
            "SELECT * FROM bottles WHERE user_id = %s ORDER BY id",
            conn,
            params=(user_id,),
        )
    else:
        df = pd.read_sql_query("SELECT * FROM bottles ORDER BY id", conn)
    conn.close()
    for col in ["vintage", "quantity", "drink_from", "drink_by", "your_rating", "purchase_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def update_bottle(id, winery, wine_name, region, appellation, varietal, vintage,
                  quantity, drink_from, drink_by, your_notes, your_rating,
                  expert_notes, user_id=None, purchase_price=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        UPDATE bottles SET
            winery=%s, wine_name=%s, region=%s, appellation=%s, varietal=%s, vintage=%s,
            quantity=%s, drink_from=%s, drink_by=%s, your_notes=%s,
            your_rating=%s, expert_notes=%s, purchase_price=%s
        WHERE id=%s AND (user_id=%s OR user_id IS NULL)
    ''', (winery, wine_name, region, appellation, varietal, vintage, quantity,
          drink_from, drink_by, your_notes, your_rating, expert_notes, purchase_price, id, user_id))
    conn.commit()
    conn.close()


def log_consumption(bottle_id, winery, wine_name, vintage, varietal, region,
                    quantity, consumed_on, notes, user_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO consumption_log
            (bottle_id, winery, wine_name, vintage, varietal, region,
             quantity, consumed_on, notes, user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (bottle_id, winery, wine_name, vintage, varietal, region,
          quantity, consumed_on, notes, user_id))
    conn.commit()
    conn.close()


def get_consumption_log(user_id: str | None = None) -> pd.DataFrame:
    conn = psycopg2.connect(DATABASE_URL)
    if user_id:
        df = pd.read_sql_query(
            "SELECT * FROM consumption_log WHERE user_id = %s ORDER BY consumed_on DESC, id DESC",
            conn,
            params=(user_id,),
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM consumption_log ORDER BY consumed_on DESC, id DESC", conn
        )
    conn.close()
    return df


def delete_bottle(id, user_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "DELETE FROM bottles WHERE id=%s AND (user_id=%s OR user_id IS NULL)",
        (id, user_id)
    )
    conn.commit()
    conn.close()
