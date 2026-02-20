import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import os

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

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
            expert_notes TEXT
        )
    ''')
    conn.commit()
    conn.close()


def add_bottle(winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO bottles (winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes))
    conn.commit()
    conn.close()


def get_bottles():
    conn = psycopg2.connect(DATABASE_URL)
    df = pd.read_sql_query("SELECT * FROM bottles ORDER BY id", conn)
    conn.close()
    for col in ["vintage", "quantity", "drink_from", "drink_by", "your_rating"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def update_bottle(id, winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        UPDATE bottles SET
            winery=%s, wine_name=%s, region=%s, appellation=%s, varietal=%s, vintage=%s,
            quantity=%s, drink_from=%s, drink_by=%s, your_notes=%s,
            your_rating=%s, expert_notes=%s
        WHERE id=%s
    ''', (winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes, id))
    conn.commit()
    conn.close()


def delete_bottle(id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM bottles WHERE id=%s", (id,))
    conn.commit()
    conn.close()