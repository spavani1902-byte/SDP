import re
import pandas as pd
from database.database import get_connection

def save_dynamic_table(file_path):

    # Step 1: Read Excel
    df = pd.read_excel(file_path, header=None)
    df = df.fillna("")
    data = df.values.tolist()

    # 🔍 DEBUG (optional but useful)
    print("=== RAW DATA PREVIEW ===")
    for i in range(min(10, len(data))):
        print(i, data[i])

    # Step 2: Extract Main Heading (Table Name)
    main_heading = ""

    for row in data:
        if str(row[0]).strip():
            main_heading = str(row[0]).strip()
            break

    if not main_heading:
        raise Exception("No table heading found")

    table_name = main_heading.lower()

    # clean table name
    table_name = re.sub(r'[^a-z0-9_]', '_', table_name)
    table_name = re.sub(r'_+', '_', table_name)
    table_name = table_name.strip('_')

    # Step 3: Detect Header Row Dynamically
    header_index = None

    for i, row in enumerate(data):
        non_empty = [cell for cell in row if str(cell).strip() != ""]

        if len(non_empty) >= 2:  # header usually has multiple columns
            header_index = i
            break

    if header_index is None:
        raise Exception("Header row not found")

    columns = data[header_index]

    # ✅ KEEP column cleaning
    columns = [str(col).strip().replace(" ", "_") for col in columns]

    rows = data[header_index + 1:]

    # Step 4: Handle Broken Rows
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

    # 🚨 Safety check
    if not clean_rows:
        raise Exception("No valid data rows found after processing")

    # Step 5: Create DataFrame
    df_clean = pd.DataFrame(clean_rows, columns=columns)

    # Step 6: Store in Database
    conn = get_connection()
    df_clean.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

    print(f"✅ Table '{table_name}' created successfully!")

    return table_name