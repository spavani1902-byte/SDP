import re
import pandas as pd
from database.database import get_connection

def save_dynamic_table(file_path):
    
    # Step 1: Read Excel
    df = pd.read_excel(file_path, header=None)
    df = df.fillna("")
    data = df.values.tolist()

    # Step 2: Extract Main Heading (Table Name)
    main_heading = str(data[0][0]).strip()

    table_name = main_heading.lower()

    # remove everything except letters, numbers, underscore
    table_name = re.sub(r'[^a-z0-9_]', '_', table_name)

    # remove multiple underscores
    table_name = re.sub(r'_+', '_', table_name)

    # remove leading/trailing underscores
    table_name = table_name.strip('_')

    # Step 3: Extract Sub Headings (Columns)
    columns = data[4]   # adjust index if needed

    # Clean column names
    columns = [str(col).strip().replace(" ", "_") for col in columns]

    # Step 4: Extract Data Rows
    rows = data[5:]

    # Step 5: Handle Broken Rows
    clean_rows = []
    current_row = None

    for row in rows:
        if row[0] != "":
            if current_row:
                clean_rows.append(current_row)
            current_row = list(row)
        else:
            for i in range(len(row)):
                if row[i] != "":
                    current_row[i] = str(current_row[i]) + " " + str(row[i])

    if current_row:
        clean_rows.append(current_row)

    # Step 6: Create DataFrame
    df_clean = pd.DataFrame(clean_rows, columns=columns)

    # Step 7: Store in Database
    conn = get_connection()
    df_clean.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

    print(f"Table '{table_name}' created successfully!")

    return table_name