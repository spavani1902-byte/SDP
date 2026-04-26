"""
table_loader.py
Detects file type and returns list[pd.DataFrame]
Supports: Excel, PDF, Word
"""

import pandas as pd
from pathlib import Path


# ─────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────
def get_dataframes_from_file(file_path: str):

    ext = Path(file_path).suffix.lower()

    if ext in (".xlsx", ".xls"):
        return _from_excel(file_path)

    elif ext in (".pdf", ".docx", ".doc"):
        return _from_docling(file_path)

    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ─────────────────────────────────────────────
# EXCEL
# ─────────────────────────────────────────────
def _from_excel(file_path: str):

    xl = pd.ExcelFile(file_path)
    result = []

    for sheet in xl.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet, header=None)

        # 🔥 DETECT TIMETABLE (based on content, NOT filename)
        sample_text = " ".join(df.head(10).astype(str).values.flatten()).lower()

        is_timetable = any(day in sample_text for day in [
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"
        ])

        if is_timetable:
            # ✅ KEEP RAW STRUCTURE (IMPORTANT)
            df = df.fillna("").astype(str)
            result.append(df)
        else:
            # ✅ IQAC / structured tables → clean
            df = _clean(df)
            if not df.empty:
                result.append(df)

    return result


# ─────────────────────────────────────────────
# DOC / PDF (Docling)
# ─────────────────────────────────────────────
def _from_docling(file_path: str):

    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(file_path)

    doc = result.document
    tables = []

    # 🔥 USE DIRECT TABLE ACCESS (IMPORTANT FIX)
    for table in doc.tables:

        try:
            # ✅ PASS DOCUMENT (you already did right here)
            df = table.export_to_dataframe(doc)

            # 🔥 IMPORTANT: don't over-clean early
            if df is not None and not df.empty:
                df = df.fillna("").astype(str)
                tables.append(df)

        except Exception as e:
            print("⚠️ Table extraction error:", e)

    # 🔥 DEBUG: SHOW RAW TABLE
    print("\n🧪 RAW TABLES FROM DOCLING:")
    for i, t in enumerate(tables):
        print(f"\nTABLE {i+1}")
        print(t.head(20))

    return tables


# ─────────────────────────────────────────────
# CLEAN + HEADER FIX
# ─────────────────────────────────────────────
def _clean(df: pd.DataFrame):

    # remove empty rows/cols
    df = df.dropna(how="all").dropna(axis=1, how="all")

    if df.empty:
        return df

    # 🔥 SAFE CONVERSION
    df = df.fillna("")
    df = df.astype(str)

    df = df.apply(lambda col: col.map(
        lambda x: "" if str(x).strip().lower() in ("nan", "none", "nat", "<na>")
        else str(x).strip()
    ))

    # remove empty rows again
    df = df[df.apply(lambda r: any(v != "" for v in r), axis=1)].reset_index(drop=True)

    if df.empty:
        return df

    # ─────────────────────────────────────────
    # 🔥 SMART HEADER DETECTION (FIXED)
    # ─────────────────────────────────────────
    header_found = False

    for i in range(min(10, len(df))):
        row = df.iloc[i].astype(str).str.lower()

        # detect IQAC header (CO + BL present)
        if any("co" in x for x in row) and any("bl" in x for x in row):
            df.columns = [str(v).strip() for v in df.iloc[i]]
            df = df[i+1:].reset_index(drop=True)
            header_found = True
            break

    # fallback
    if not header_found:
        df.columns = [f"col_{i}" for i in range(len(df.columns))]

    # clean column names
    df.columns = [str(c).strip() for c in df.columns]

    # remove empty columns
    df = df.loc[:, (df != "").any(axis=0)]

    return df.reset_index(drop=True)


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────
def _is_numeric(v):

    try:
        float(str(v).replace(",", ""))
        return True
    except:
        return False