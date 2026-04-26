"""
Timetable Extractor (Robust Version)
Handles messy Excel (shifted columns, empty cells)
"""

import re


def extract_timetable_from_df(df):

    df = df.fillna("").astype(str)

    records = []

    # ======================
    # HEADER DETECTION
    # ======================
    header_row = None

    for i in range(len(df)):
        row_text = " ".join(df.iloc[i])
        if re.search(r'\d{1,2}[:\.\-]\d{2}', row_text):
            header_row = i
            break

    if header_row is None:
        print("❌ Header not found")
        return []

    print("✅ Header row:", header_row)

    time_slots = df.iloc[header_row].values

    # ======================
    # MAIN EXTRACTION
    # ======================
    for i in range(header_row + 1, len(df)):

        row = df.iloc[i].values

        # 🔥 detect day anywhere in row
        day = None
        for cell in row:
            c = str(cell).strip().lower()
            if c in ["monday","tuesday","wednesday","thursday","friday","saturday"]:
                day = c.capitalize()
                break

        if not day:
            continue

        print(f"📅 {day}")

        for j in range(len(row)):

            subject = str(row[j]).strip()

            if subject == "":
                continue

            # skip day cell
            if subject.lower() == day.lower():
                continue

            # safe index
            if j >= len(time_slots):
                continue

            time = str(time_slots[j]).strip()

            # skip invalid time cells
            if not re.search(r'\d', time):
                continue

            records.append({
                "day": day,
                "time": time,
                "subject": subject,
                "faculty": ""
            })

    return records