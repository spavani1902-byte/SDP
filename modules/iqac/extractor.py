import pandas as pd
import re

def excel_to_bridge(path):

    df = pd.read_excel(path, header=None)
    df = df.fillna("")

    extracted = []
    current_main = 1
    current_part = "A"

    for _, row in df.iterrows():

        row_values = [str(x).strip() for x in row]
        line = " ".join(row_values).upper()

        # ======================
        # PART DETECTION
        # ======================
        if "PART-A" in line or "PART A" in line:
            current_part = "A"
            continue

        elif "PART-B" in line or "PART B" in line:
            current_part = "B"
            continue

        # ======================
        # QUESTION DETECTION
        # ======================
        qcell = row_values[0] if len(row_values) > 0 else ""

        match = re.match(r'(\d+)[\.\)]\s*([a-jA-J])', qcell)
        if match:
            current_main = int(match.group(1))
            sub = match.group(2).lower()
            qno = f"{current_main}{sub}"

        elif re.match(r'^\(?([a-jA-J])\)', qcell):
            sub = qcell[0].lower()
            qno = f"{current_main}{sub}"

        elif re.match(r'^\d+$', qcell):
            current_main = int(qcell)
            qno = str(current_main)

        else:
            continue

        # ======================
        # CO DETECTION
        # ======================
        co_match = re.search(r'CO\s*\d+', line, re.IGNORECASE)
        co = co_match.group(0).replace(" ", "").upper() if co_match else "CO1"

        # ======================
        # BLOOM LEVEL
        # ======================
        bl_match = re.search(r'\bL\s*([1-6])\b', line, re.IGNORECASE)
        bl = f"L{bl_match.group(1)}" if bl_match else "L1"

        # ======================
        # MARKS
        # ======================
        marks = 1
        for val in reversed(row_values):
            if val.isdigit():
                num = int(val)
                if 1 <= num <= 10:
                    marks = num
                    break

        # ======================
        # APPEND
        # ======================
        extracted.append([qno, marks, co, bl, current_part])

    # ======================
    # SAVE BRIDGE FILE
    # ======================
    out = pd.DataFrame(extracted, columns=["Qno", "Marks", "CO", "BL", "Part"])
    out.to_excel("bridge.xlsx", index=False)

    print("✅ Extracted rows:", len(out))
    print(out.head())

    return "bridge.xlsx"