"""
modules/committees/processor.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pandas as pd
from table_loader import get_dataframes_from_file
from modules.committees.extractor import extract_committees_from_df


def process_committees(file_path: str) -> pd.DataFrame:
    dfs = get_dataframes_from_file(file_path)
    if not dfs:
        raise ValueError("No tables found in file.")

    records = []
    for df in dfs:
        records.extend(extract_committees_from_df(df))

    if not records:
        raise ValueError("No committee data found in document.")

    return pd.DataFrame(records).dropna(how="all").reset_index(drop=True)