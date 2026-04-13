from .processor import process_iqac

def handle_iqac(file_path):
    """
    Handles IQAC processing flow.
    Calls processor and returns dataframe + table name
    """

    try:
        df, table_name = process_iqac(file_path)
        return df, table_name

    except Exception as e:
        print("❌ IQAC Error:", e)
        raise Exception(f"IQAC processing failed: {e}")