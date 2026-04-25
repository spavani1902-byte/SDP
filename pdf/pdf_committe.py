import pdfplumber
import pandas as pd
import re


def clean_text(x):
    return re.sub(r'\s+', ' ', str(x)).strip() if x else ""


def is_valid_row(row):
    text = " ".join([str(i) for i in row if i])
    return len(text.strip()) > 2


def process_pdf(pdf_path, output_path):

    extracted_rows = []
    table_mode = False

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:

            # =========================
            # STEP 1: TRY TABLE EXTRACTION
            # =========================
            tables = page.extract_tables()

            if tables:
                table_mode = True

                for table in tables:
                    if not table:
                        continue

                    for row in table:
                        if not is_valid_row(row):
                            continue

                        cleaned = [clean_text(cell) for cell in row]
                        extracted_rows.append(cleaned)

            # =========================
            # STEP 2: FALLBACK TEXT MODE
            # =========================
            else:
                text = page.extract_text()

                if not text:
                    continue

                lines = text.split("\n")

                for line in lines:
                    line = clean_text(line)

                    if not line:
                        continue

                    # Split loosely by spacing, dash, colon
                    parts = re.split(r'\s{2,}|[-:|]', line)

                    parts = [p.strip() for p in parts if p.strip()]

                    if len(parts) == 0:
                        continue

                    extracted_rows.append(parts)

    # =========================
    # NORMALIZE COLUMN LENGTH
    # =========================
    max_cols = max(len(r) for r in extracted_rows)

    normalized = []
    for r in extracted_rows:
        r = r + [""] * (max_cols - len(r))  # pad missing columns
        normalized.append(r)

    # =========================
    # CREATE DATAFRAME
    # =========================
    df = pd.DataFrame(normalized)

    # Try to use first row as header (if meaningful)
    if len(df) > 0:
        df.columns = df.iloc[0]
        df = df[1:]

    # Clean empty rows
    df = df.dropna(how="all")

    # Reset index
    df = df.reset_index(drop=True)

    # =========================
    # SAVE TO EXCEL
    # =========================
    df.to_excel(output_path, index=False)

    print(f"✅ Generic committee extraction done → {output_path}")

    return output_path


# =========================
# RUN DIRECTLY
# =========================
if __name__ == "__main__":
    process_pdf("input.pdf", "output.xlsx")