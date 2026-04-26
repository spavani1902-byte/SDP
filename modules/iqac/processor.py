import pandas as pd
from table_loader import get_dataframes_from_file
from modules.iqac.extractor import extract_iqac_from_df


def process_iqac(file_path: str):

    dfs = get_dataframes_from_file(file_path)

    if not dfs:
        raise ValueError("No tables found.")

    print("\n📂 DEBUG TABLES")

    for i, df in enumerate(dfs):
        print(f"\nTABLE {i+1}")
        print(df.head(10))

    records = []

    for df in dfs:
        records.extend(extract_iqac_from_df(df))

    if not records:
        raise ValueError("No IQAC data found.")

    print("\n📦 FINAL RECORDS")
    print(records)

    result = pd.DataFrame(records)

    result = result.rename(columns={
        "qno": "QNo",
        "co": "CO",
        "bl": "BL",
        "marks": "Marks",
        "part": "Part"
    })

    return result[["QNo", "CO", "BL", "Marks", "Part"]]