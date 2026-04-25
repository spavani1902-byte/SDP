import time
import pandas as pd
from .committees import extract_committees


def handle_committees(file_path):

    print("🚀 Starting Committees Processing...")

    df = extract_committees(file_path)

    if df is None:
        raise Exception("No data returned")

    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    if df.empty:
        raise Exception("No Committees data extracted")

    table_name = f"committees_{int(time.time())}"

    print("✅ Committees processed successfully")

    return df, table_name