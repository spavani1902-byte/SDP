import pdfplumber
import pandas as pd
import re


def extract_timetable(pdf_path, output_excel):
    try:
        # =========================
        # PART 1: TABLE EXTRACTION (UNCHANGED)
        # =========================
        table_data = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()

                if table:
                    for row in table:
                        cleaned_row = []
                        for cell in row:
                            if cell is None:
                                cleaned_row.append("")
                            else:
                                cleaned_row.append(str(cell).strip())
                        table_data.append(cleaned_row)

        if not table_data:
            return None

        df_table = pd.DataFrame(table_data)

        # Fill merged cells manually
        for i in range(len(df_table)):
            last_val = ""
            for j in range(len(df_table.columns)):
                val = df_table.iat[i, j]
                if val == "" or pd.isna(val):
                    df_table.iat[i, j] = last_val
                else:
                    last_val = val

        # =========================
        # PART 2: FACULTY EXTRACTION (ROBUST)
        # =========================
        full_text = ""

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

        # Clean broken words
        full_text = re.sub(r"Wednesd\s+ay", "Wednesday", full_text)

        # Extract ONLY the relevant block
        start = full_text.find("Name of the Subject")
        end = full_text.find("Class Teacher")

        if start == -1:
            faculty_pairs = []
        else:
            if end == -1:
                section = full_text[start:]
            else:
                section = full_text[start:end]

            # =========================
            # Extract subjects and faculty separately
            # =========================
            faculty_names = re.findall(r"(Dr\.\s*[A-Za-z\. ]+|Mr\.\s*[A-Za-z\. ]+|Mrs\.\s*[A-Za-z\. ]+)", section)

            # Remove faculty names to isolate subjects
            temp = section
            for name in faculty_names:
                temp = temp.replace(name, "|")

            subjects = [s.strip() for s in temp.split("|") if s.strip()]

            # Pair them
            faculty_pairs = []
            for i in range(min(len(subjects), len(faculty_names))):
                faculty_pairs.append([subjects[i], faculty_names[i]])

        df_faculty = pd.DataFrame(faculty_pairs, columns=["Subject", "Faculty"])

        # =========================
        # PART 3: SAVE EXCEL
        # =========================
        with pd.ExcelWriter(output_excel) as writer:
            df_table.to_excel(writer, sheet_name="Timetable", index=False, header=False)
            df_faculty.to_excel(writer, sheet_name="Faculty Mapping", index=False)

        return output_excel

    except Exception as e:
        print("❌ Error:", e)
        return None