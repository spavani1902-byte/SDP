import pandas as pd
import re


# ==========================
# 🔹 GET ABBREVIATION (ONLY CAPITAL LETTERS)
# ==========================
def get_abbreviation(text):
    text = text.replace("&", "")
    return "".join([c for c in text if c.isupper()])


# ==========================
# 🔹 CLEAN TEXT
# ==========================
def clean_text(text):
    return re.sub(r'\(.*?\)', '', str(text)).strip()


# ==========================
# 🔹 MAIN FUNCTION
# ==========================
def extract_timetable(path):

    print("🚀 Starting Timetable Processing...")

    df = pd.read_excel(path, header=None)
    df = df.fillna("")

    # ==========================
    # 🔹 STEP 1: FIND HEADER
    # ==========================
    header_row = None

    for i in range(len(df)):
        row_text = " ".join(map(str, df.iloc[i].values))
        if re.search(r'\d{1,2}:\d{2}', row_text):
            header_row = i
            break

    if header_row is None:
        raise Exception("❌ Header row not found")

    print("✅ Header row:", header_row)

    time_slots = df.iloc[header_row].values

    # ==========================
    # 🔹 STEP 2: EXTRACT TIMETABLE
    # ==========================
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    structured = []

    for i in range(header_row + 1, len(df)):

        row = df.iloc[i].values
        day = str(row[0]).strip()

        # stop when faculty section starts
        if "name of the subject" in day.lower():
            break

        if day in days:

            for j in range(1, len(row)):

                subject = str(row[j]).strip()
                time = str(time_slots[j]).strip()

                if not subject:
                    continue

                if subject.lower() in ["lunch", "break"]:
                    continue

                structured.append({
                    "day": day,
                    "time": time,
                    "subject": subject,
                    "faculty": ""
                })

    print("✅ Timetable rows:", len(structured))

    # ==========================
    # 🔹 STEP 3: EXTRACT FACULTY (DYNAMIC 🔥)
    # ==========================
    faculty_map = {}
    faculty_start = None

    for i in range(len(df)):
        row_text = " ".join(df.iloc[i].astype(str)).lower()

        if "name of the subject" in row_text:
            faculty_start = i + 1
            break

    if faculty_start is not None:

        print("✅ Faculty section starts at:", faculty_start)

        for i in range(faculty_start, len(df)):

            # remove empty cells
            row = [str(x).strip() for x in df.iloc[i].values if str(x).strip() != ""]

            if len(row) < 2:
                continue

            # 🔥 dynamic pair scanning
            for j in range(len(row) - 1):

                subject = clean_text(row[j])
                faculty = row[j + 1]

                if (
                    subject
                    and len(subject) > 3
                    and any(c.isalpha() for c in subject)
                    and any(x in faculty.lower() for x in ["dr", "mr", "mrs", "prof"])
                ):
                    faculty = faculty.split("/")[0].strip()
                    faculty_map[subject] = faculty

    print("📌 FINAL Faculty map:", faculty_map)

    # ==========================
    # 🔹 STEP 4: ABBREVIATION MAP
    # ==========================
    abbr_map = {}

    for subject, faculty in faculty_map.items():
        abbr = get_abbreviation(subject)
        if abbr:
            abbr_map[abbr] = faculty

    print("📌 ABBR MAP:", abbr_map)

    # ==========================
    # 🔹 STEP 5: MATCH SUBJECT → FACULTY
    # ==========================
    for item in structured:

        sub = item["subject"].replace("&", "")
        sub_abbr = get_abbreviation(sub)

        base_sub = sub_abbr.replace("LAB", "")

        # direct match
        if sub_abbr in abbr_map:
            item["faculty"] = abbr_map[sub_abbr]

        # fallback (LAB → THEORY)
        elif base_sub in abbr_map:
            item["faculty"] = abbr_map[base_sub]

    print("🎯 Timetable extraction completed")

    # ==========================
    # 🔹 FINAL OUTPUT
    # ==========================
    df_final = pd.DataFrame(structured)

    if df_final.empty:
        raise Exception("❌ No timetable data extracted")

    return df_final