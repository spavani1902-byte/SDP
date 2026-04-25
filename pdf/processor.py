import pdfplumber
import pandas as pd


def process_pdf(pdf_path, output_path):

    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:

            # Try extracting table first
            tables = page.extract_tables()

            if tables:
                for table in tables:
                    for row in table:
                        clean_row = [str(cell).strip() if cell else "" for cell in row]
                        rows.append(clean_row)

            else:
                # fallback → text lines as single column
                text = page.extract_text()
                if text:
                    for line in text.split("\n"):
                        rows.append([line.strip()])

    if not rows:
        raise Exception("❌ No data extracted from PDF")

    df = pd.DataFrame(rows)

    print("✅ Extracted rows for IQAC:", len(df))
    print(df.head())

    df.to_excel(output_path, index=False, header=False)

    print("✅ Excel (RAW FORMAT) created:", output_path)

    return output_path