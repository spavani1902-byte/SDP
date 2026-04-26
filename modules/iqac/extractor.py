"""
extractor.py — FINAL IQAC EXTRACTOR (TABLE + TEXT MARKS FIX)
"""

import re
import pandas as pd
from typing import List


def extract_iqac_from_df(df: pd.DataFrame) -> List[dict]:

    if df is None or df.empty:
        return []

    df = df.fillna("").astype(str)

    last_co = "CO1"
    last_bl = "L1"

    current_main = None
    in_part_b = False

    results = []
    seen = set()

    for _, row in df.iterrows():

        # 🔥 STRONG ROW TEXT (IMPORTANT FIX)
        row_text = " ".join([str(x) for x in row.values])
        row_text = row_text.replace("\n", " ")
        row_text = re.sub(r'\s+', ' ', row_text)
        row_text = re.sub(r'[*_`]', '', row_text).upper().strip()

        if not row_text:
            continue

        # -------------------------
        # PART B DETECTION
        # -------------------------
        if "PART-B" in row_text or "PART B" in row_text:
            in_part_b = True
            continue

        # -------------------------
        # CO
        # -------------------------
        co_match = re.search(r'CO\s*(\d+)', row_text)
        if co_match:
            last_co = f"CO{co_match.group(1)}"

        # -------------------------
        # BL
        # -------------------------
        bl_match = re.search(r'\bL[-\s]?([1-6])\b', row_text)
        if bl_match:
            last_bl = f"L{bl_match.group(1)}"

        # -------------------------
        # CLEAN CELLS
        # -------------------------
        cells = [
            re.sub(r'[*_`]', '', c).upper().strip()
            for c in row.values
        ]

        qno = None
        part = None

        # -------------------------
        # 2.a pattern
        # -------------------------
        for cell in cells:
            m = re.search(r'(\d+)\s*\.\s*\(?([A-J])', cell)
            if m:
                current_main = m.group(1)
                qno = f"{current_main}{m.group(2).lower()}"
                part = "B"
                in_part_b = True
                break

        # -------------------------
        # b) continuation
        # -------------------------
        if not qno and in_part_b and current_main:
            for cell in cells:
                m = re.match(r'^\(?([A-J])', cell)
                if m:
                    qno = f"{current_main}{m.group(1).lower()}"
                    part = "B"
                    break

        # -------------------------
        # a) Part A
        # -------------------------
        if not qno and not in_part_b:
            for cell in cells:
                m = re.match(r'^\(?([A-J])', cell)
                if m:
                    qno = f"1{m.group(1).lower()}"
                    part = "A"
                    break

        # -------------------------
        # 🔥 MARKS FIX (FINAL)
        # -------------------------
        marks = None

        # Strict [3M]
        marks_match = re.search(r'\[(\d+)\s*M\]', row_text)

        # Loose 3M
        if not marks_match:
            marks_match = re.search(r'(\d+)\s*M', row_text)

        if marks_match:
            marks = int(marks_match.group(1))
        else:
            # fallback
            marks = 1 if part == "A" else 5

        # -------------------------
        # SAVE
        # -------------------------
        if qno and qno not in seen:
            results.append({
                "qno": qno,
                "co": last_co,
                "bl": last_bl,
                "marks": marks,
                "part": part
            })
            seen.add(qno)

    # -------------------------
    # SORT
    # -------------------------
    def sort_key(x):
        num = int(re.match(r'\d+', x["qno"]).group())
        sub = x["qno"][-1]
        return (num, sub)

    return sorted(results, key=sort_key)