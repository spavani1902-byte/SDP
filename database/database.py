import sqlite3
import pandas as pd

# 🔹 Create / Connect Database
def get_connection(db_name="C:/Users/S Laxmi Narayana/OneDrive/Desktop/GDPS/iqac.db"):
    conn = sqlite3.connect(db_name)
    return conn


# 🔹 Store DataFrame into Database
def store_table(df, table_name, db_name="C:/Users/S Laxmi Narayana/OneDrive/Desktop/GDPS/iqac.db"):
    conn = get_connection(db_name)
    
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"Table '{table_name}' stored successfully.")
    except Exception as e:
        print("Error storing table:", e)
    
    finally:
        conn.close()


# 🔹 Append Data (optional)
def append_table(df, table_name, db_name="iqac.db"):
    conn = get_connection(db_name)
    
    try:
        df.to_sql(table_name, conn, if_exists="append", index=False)
        print(f"Data appended to '{table_name}'.")
    except Exception as e:
        print("Error appending data:", e)
    
    finally:
        conn.close()


# 🔹 Read Table from Database
def read_table(table_name, db_name="iqac.db"):
    conn = get_connection(db_name)
    
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        return df
    except Exception as e:
        print("Error reading table:", e)
        return None
    
    finally:
        conn.close()


# 🔹 Delete Table (optional)
def delete_table(table_name, db_name="iqac.db"):
    conn = get_connection(db_name)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        print(f"Table '{table_name}' deleted.")
    except Exception as e:
        print("Error deleting table:", e)
    
    finally:
        conn.close()


# 🔹 List all tables (useful for debugging)
def list_tables(db_name="iqac.db"):
    conn = get_connection(db_name)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Database function called")
        return [t[0] for t in tables]
    except Exception as e:
        print("Error fetching tables:", e)
        return []
    
    finally:
        conn.close()