from .committees import save_dynamic_table
from database.database import read_table

def handle_committees(file_path):
    """
    Handles Committees processing flow.
    Saves table in DB and returns dataframe + table name
    """

    try:
        table_name = save_dynamic_table(file_path)

        df = read_table(table_name)

        if df is None or df.empty:
            raise Exception("No data found in generated table")

        return df, table_name

    except Exception as e:
        print("❌ Committees Error:", e)
        raise Exception(f"Committees processing failed: {e}")