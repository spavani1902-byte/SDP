import pandas as pd
import re

def parse_excel_full(path):

    # Read bridge file
    df = pd.read_excel(path)
    df = df.fillna("")

    parsed = []

    for _, row in df.iterrows():

        # ======================
        # QUESTION NUMBER CLEANING
        # ======================
        q_raw = str(row.get("Qno", "")).strip()

        # Match patterns like 1, 1a, 1.a
        match = re.match(r'(\d+)\.?\s*([a-z])?', q_raw, re.IGNORECASE)

        if not match:
            continue

        num = match.group(1)
        sub = match.group(2).lower() if match.group(2) else ""

        q = num + sub   # final format → 1a, 2b

        # ======================
        # CO CLEANING
        # ======================
        co = str(row.get("CO", "CO1")).strip().upper()

        if co == "" or co.lower() == "nan":
            co = "CO1"

        # ======================
        # BLOOM LEVEL CLEANING
        # ======================
        bl = str(row.get("BL", "L1")).strip().upper()

        if not re.match(r'L[1-6]', bl):
            bl = "L1"

        # ======================
        # MARKS CLEANING
        # ======================
        marks = row.get("Marks", 1)

        try:
            marks = int(marks)
        except:
            marks = 1

        if marks <= 0 or marks > 20:
            marks = 1

        # ======================
        # PART CLEANING
        # ======================
        part = str(row.get("Part", "A")).strip().upper()

        if part not in ["A", "B"]:
            part = "A"

        # ======================
        # FINAL RECORD
        # ======================
        parsed.append({
            "q": q,
            "co": co,
            "level": bl,
            "marks": marks,
            "part": part
        })

    # ======================
    # DEBUG
    # ======================
    print("✅ Parsed records:", len(parsed))

    if len(parsed) < 3:
        print("⚠️ Warning: Too few questions parsed")

    return parsed