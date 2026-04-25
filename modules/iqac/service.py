import time
import pandas as pd
from .processor import process_iqac


def handle_iqac(file_path):

    print("🚀 Starting IQAC Processing...")

    df, _ = process_iqac(file_path)

    # Ensure DataFrame
    if df is None:
        raise Exception("No data returned")

    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    if df.empty:
        raise Exception("No IQAC data extracted")

    # Unique table name
    table_name = f"iqac_{int(time.time())}"

    print("✅ IQAC processed successfully")

    return df, table_name