"""
Timetable Processor
Uses table_loader + robust extraction
"""

import re
import pandas as pd
from table_loader import get_dataframes_from_file
from modules.timetable.extractor import extract_timetable_from_df


def process_timetable(file_path: str) -> pd.DataFrame:

    print("\n==============================")
    print("📂 PROCESSING TIMETABLE")
    print("==============================")

    # ✅ use loader (IMPORTANT)
    dfs = get_dataframes_from_file(file_path)

    if not dfs:
        raise ValueError("No tables found in timetable file.")

    all_records = []

    for i, df in enumerate(dfs):

        print(f"\n📊 TABLE {i+1}")
        print(df.head(10))

        records = extract_timetable_from_df(df)

        print(f"✅ Extracted {len(records)} rows")

        all_records.extend(records)

    if not all_records:
        raise ValueError("No timetable data found in document.")

    result = pd.DataFrame(all_records)

    print("\n🎯 FINAL OUTPUT:")
    print(result.head())

    return result