"""
modules/committees/extractor.py
Extract full committee table rows. No AI.
"""

import re
import pandas as pd


def _find_col(df: pd.DataFrame, *hints: str) -> str | None:
    cols = [str(c).lower() for c in df.columns]
    for h in hints:
        for i, c in enumerate(cols):
            if h.lower() in c:
                return df.columns[i]
    return None


def _cell(row, col) -> str | None:
    v = str(row[col]).strip() if col and col in row.index else ""
    return v or None


def extract_committees_from_df(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    df = df.copy()
    df.columns = [re.sub(r"\s+", " ", str(c).lower().strip()) for c in df.columns]

    col_sno   = _find_col(df, "sno", "s.no", "sl", "no")
    col_name  = _find_col(df, "name", "member")
    col_desig = _find_col(df, "designation", "design", "post", "position", "title")
    col_role  = _find_col(df, "role", "function", "responsibility", "convener", "member")
    col_dept  = _find_col(df, "department", "dept", "branch", "division")
    col_cont  = _find_col(df, "contact", "email", "phone", "mobile")

    # If key columns not found, treat every column as-is and return raw rows
    if not col_name:
        records = []
        for _, row in df.iterrows():
            vals = {str(c): (str(v).strip() or None) for c, v in row.items()}
            if any(v for v in vals.values()):
                records.append(vals)
        return records

    records = []
    for _, row in df.iterrows():
        name = _cell(row, col_name)
        if not name:
            continue
        records.append({
            "sno":         _cell(row, col_sno),
            "name":        name,
            "designation": _cell(row, col_desig),
            "role":        _cell(row, col_role),
            "department":  _cell(row, col_dept),
            "contact":     _cell(row, col_cont),
        })

    return records