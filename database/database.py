import sqlite3
import pandas as pd
import os

# 🔥 FIXED ABSOLUTE PATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "iqac.db")


def get_connection(db_name=DB_PATH):
    print("📂 USING DB:", db_name)   # 🔥 debug
    return sqlite3.connect(db_name)


def store_table(df, table_name, db_name=DB_PATH):
    conn = get_connection(db_name)
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    finally:
        conn.close()


def append_table(df, table_name, db_name=DB_PATH):
    conn = get_connection(db_name)
    try:
        df.to_sql(table_name, conn, if_exists="append", index=False)
    finally:
        conn.close()


def read_table(table_name, db_name=DB_PATH):
    conn = get_connection(db_name)
    try:
        return pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception as e:
        print("Error reading table:", e)
        return None
    finally:
        conn.close()


def delete_table(table_name, db_name=DB_PATH):
    conn = get_connection(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
    finally:
        conn.close()


def list_tables(db_name=DB_PATH):
    conn = get_connection(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [t[0] for t in cursor.fetchall()]
    finally:
        conn.close()