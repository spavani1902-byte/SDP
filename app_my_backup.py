import os
import pdfplumber
import pandas as pd
import re
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


# =========================
# IQAC FUNCTION (UNCHANGED)
# =========================
def process_iqac_pdf(pdf_path, output_path):

    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()

            if tables:
                for table in tables:
                    for row in table:
                        clean_row = [str(cell).strip() if cell else "" for cell in row]
                        rows.append(clean_row)
            else:
                text = page.extract_text()
                if text:
                    for line in text.split("\n"):
                        rows.append([line.strip()])

    if not rows:
        raise Exception("No data extracted")

    df = pd.DataFrame(rows)
    df.to_excel(output_path, index=False, header=False)

    return output_path


# =========================
# TIMETABLE FUNCTION (UNCHANGED)
# =========================
def extract_timetable(pdf_path, output_excel):

    table_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    cleaned_row = []
                    for cell in row:
                        cleaned_row.append(str(cell).strip() if cell else "")
                    table_data.append(cleaned_row)

    if not table_data:
        return None

    df_table = pd.DataFrame(table_data)

    for i in range(len(df_table)):
        last_val = ""
        for j in range(len(df_table.columns)):
            val = df_table.iat[i, j]
            if val == "" or pd.isna(val):
                df_table.iat[i, j] = last_val
            else:
                last_val = val

    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    full_text = re.sub(r"Wednesd\s+ay", "Wednesday", full_text)

    start = full_text.find("Name of the Subject")
    end = full_text.find("Class Teacher")

    if start == -1:
        faculty_pairs = []
    else:
        section = full_text[start:end] if end != -1 else full_text[start:]

        faculty_names = re.findall(r"(Dr\.\s*[A-Za-z\. ]+|Mr\.\s*[A-Za-z\. ]+|Mrs\.\s*[A-Za-z\. ]+)", section)

        temp = section
        for name in faculty_names:
            temp = temp.replace(name, "|")

        subjects = [s.strip() for s in temp.split("|") if s.strip()]

        faculty_pairs = []
        for i in range(min(len(subjects), len(faculty_names))):
            faculty_pairs.append([subjects[i], faculty_names[i]])

    df_faculty = pd.DataFrame(faculty_pairs, columns=["Subject", "Faculty"])

    with pd.ExcelWriter(output_excel) as writer:
        df_table.to_excel(writer, sheet_name="Timetable", index=False, header=False)
        df_faculty.to_excel(writer, sheet_name="Faculty Mapping", index=False)

    return output_excel


# =========================
# COMMITTEE FUNCTION (UNCHANGED)
# =========================
def process_committee_pdf(pdf_path, output_path):

    def clean_text(x):
        return re.sub(r'\s+', ' ', str(x)).strip() if x else ""

    def is_valid_row(row):
        text = " ".join([str(i) for i in row if i])
        return len(text.strip()) > 2

    extracted_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:

            tables = page.extract_tables()

            if tables:
                for table in tables:
                    for row in table:
                        if not is_valid_row(row):
                            continue
                        cleaned = [clean_text(cell) for cell in row]
                        extracted_rows.append(cleaned)
            else:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")

                for line in lines:
                    line = clean_text(line)
                    if not line:
                        continue

                    parts = re.split(r'\s{2,}|[-:|]', line)
                    parts = [p.strip() for p in parts if p.strip()]

                    if parts:
                        extracted_rows.append(parts)

    max_cols = max(len(r) for r in extracted_rows)

    normalized = []
    for r in extracted_rows:
        r = r + [""] * (max_cols - len(r))
        normalized.append(r)

    df = pd.DataFrame(normalized)

    if len(df) > 0:
        df.columns = df.iloc[0]
        df = df[1:]

    df = df.dropna(how="all").reset_index(drop=True)

    df.to_excel(output_path, index=False)

    return output_path


# =========================
# CONTROLLER
# =========================
def process_pdf(pdf_path, output_path, doc_type):

    if doc_type == "iqac":
        return process_iqac_pdf(pdf_path, output_path)

    elif doc_type == "timetable":
        return extract_timetable(pdf_path, output_path)

    elif doc_type == "committee":
        return process_committee_pdf(pdf_path, output_path)

    else:
        raise Exception("Invalid type")


# =========================
# FLASK ROUTE
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        file = request.files["file"]
        doc_type = request.form.get("type")

        if file.filename == "":
            return "No file selected"

        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(pdf_path)

        output_file = filename.replace(".pdf", ".xlsx")
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_file)

        process_pdf(pdf_path, output_path, doc_type)

        return send_file(output_path, as_attachment=True)

    return """
    <h2>Upload PDF</h2>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file" required><br><br>

        <select name="type" required>
            <option value="">Select Type</option>
            <option value="iqac">IQAC</option>
            <option value="timetable">Timetable</option>
            <option value="committee">Committee</option>
        </select><br><br>

        <input type="submit" value="Upload & Convert">
    </form>
    """


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)