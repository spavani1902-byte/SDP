# modules/timetable/service.py

import time
import pandas as pd
from .extractor import extract_timetable


def handle_timetable(file_path):

    print("🚀 Starting Timetable Processing...")

    # Step 1: Extract data
    df = extract_timetable(file_path)

    # Step 2: Safety (no logic change, just stability)
    if df is None:
        raise Exception("No data returned from extractor")

    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    if df.empty:
        raise Exception("No timetable data extracted")

    # Step 3: Generate unique table name
    table_name = f"timetable_{int(time.time())}"

    print("✅ Timetable processed successfully")
    print("📊 Rows extracted:", len(df))

    return df, table_name