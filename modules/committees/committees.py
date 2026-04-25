import re
import pandas as pd

def extract_committees(file_path):

    df = pd.read_excel(file_path, header=None)
    df = df.fillna("")
    data = df.values.tolist()

    print("=== RAW DATA PREVIEW ===")
    for i in range(min(10, len(data))):
        print(i, data[i])

    # Find header row
    header_index = None
    for i, row in enumerate(data):
        non_empty = [cell for cell in row if str(cell).strip() != ""]
        if len(non_empty) >= 2:
            header_index = i
            break

    if header_index is None:
        raise Exception("Header row not found")

    columns = data[header_index]
    columns = [str(col).strip().replace(" ", "_") for col in columns]

    rows = data[header_index + 1:]

    clean_rows = []
    current_row = None

    for row in rows:
        if str(row[0]).strip() != "":
            if current_row:
                clean_rows.append(current_row)
            current_row = list(row)
        else:
            if current_row:
                for i in range(len(row)):
                    if str(row[i]).strip() != "":
                        current_row[i] = str(current_row[i]) + " " + str(row[i])

    if current_row:
        clean_rows.append(current_row)

    df_clean = pd.DataFrame(clean_rows)

    if len(df_clean.columns) == len(columns):
        df_clean.columns = columns

    print("✅ Committees extracted successfully")
    print(df_clean.head())

    return df_clean   # ✅ RETURN DATAFRAME