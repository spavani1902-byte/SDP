"""
database/database.py
SQLite connection and save utility.
"""

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sdp.db")
DB_PATH = os.path.abspath(DB_PATH)


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def save_dataframe(df: pd.DataFrame, table_name: str) -> None:
    """
    Save a DataFrame to SQLite.
    Table name format expected: module_timestamp (e.g. iqac_1720000000)
    """
    conn = get_connection()
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()


def list_tables() -> list[str]:
    conn = get_connection()
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def load_table(table_name: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
    finally:
        conn.close()