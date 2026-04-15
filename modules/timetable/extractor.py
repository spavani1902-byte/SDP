import pandas as pd
import re
import json


# ======================
# HELPERS
# ======================
def normalize(text):
    return re.sub(r'\s+', '', str(text).lower())


def is_same_subject(a, b):
    a = normalize(a)
    b = normalize(b)

    for word in ["lab", "workshop"]:
        a = a.replace(word, "")
        b = b.replace(word, "")

    return a and b and (a in b or b in a)


def get_abbreviation(text):
    return "".join([c for c in str(text) if c.isalpha() and c.isupper()])


def normalize_time(t):
    return str(t).replace(" ", "")


# ======================
# MAIN FUNCTION
# ======================
def extract_timetable(path):

    print("\n🚀 Starting Timetable Processing...\n")

    df = pd.read_excel(path, header=None)
    df = df.fillna("").astype(str)
    df = df.apply(lambda col: col.map(lambda x: x.strip()))

    # ======================
    # HEADER
    # ======================
    header_row = None
    for i in range(len(df)):
        if re.search(r'\d{1,2}:\d{2}', " ".join(df.iloc[i])):
            header_row = i
            break

    print("✅ Header row:", header_row)

    time_slots = df.iloc[header_row].values

    # ======================
    # LUNCH
    # ======================
    lunch_cols = set()
    for i in range(len(df)):
        for j in range(len(df.columns)):
            if "lunch" in str(df.iat[i, j]).lower():
                lunch_cols.add(j)

    print("🍽 Lunch columns:", lunch_cols)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    structured = []

    # ======================
    # TIMETABLE EXTRACTION
    # ======================
    for i in range(header_row + 1, len(df)):

        row = df.iloc[i].values
        day = row[0].strip()

        if "name of the subject" in day.lower():
            break

        if day in days:

            print(f"\n📅 {day}")

            j = 1
            while j < len(row):

                if j in lunch_cols:
                    structured.append({
                        "day": day,
                        "time": normalize_time(time_slots[j]),
                        "subject": "LUNCH",
                        "faculty": ""
                    })
                    j += 1
                    continue

                subject = row[j].strip()

                if subject == "":
                    j += 1
                    continue

                start = normalize_time(time_slots[j]).split("-")[0]

                k = j
                while k + 1 < len(row):

                    if (k + 1) in lunch_cols:
                        break

                    if not time_slots[k + 1]:
                        break

                    next_sub = row[k + 1].strip()

                    if next_sub == "":
                        k += 1
                        continue

                    if is_same_subject(subject, next_sub):
                        k += 1
                    else:
                        break

                end = normalize_time(time_slots[k]).split("-")[-1]

                structured.append({
                    "day": day,
                    "time": f"{start}-{end}",
                    "subject": subject,
                    "faculty": ""
                })

                j = k + 1

    # ======================
    # SUBJECT + LAB TABLE
    # ======================
    subject_data = {
        "subjects": {},
        "labs": {}
    }

    faculty_start = None

    for i in range(len(df)):
        if "name of the subject" in " ".join(df.iloc[i]).lower():
            faculty_start = i + 1
            break

    print("\n📘 SUBJECT + LAB TABLE:\n")

    if faculty_start:

        for i in range(faculty_start, len(df)):

            row = df.iloc[i]
            values = [str(x).strip() for x in row if str(x).strip()]

            if not values:
                continue

            subject = values[0]
            subject_faculty = ""
            lab = ""
            lab_faculty = ""

            # SUBJECT FACULTY
            for v in values:
                if any(x in v.lower() for x in ["mr.", "mrs.", "dr."]):
                    subject_faculty = v
                    break

            # LAB
            for v in values:
                if "lab" in v.lower() or "project" in v.lower():
                    lab = v
                    break

            # LAB FACULTY
            if lab:
                idx = values.index(lab)
                for v in values[idx + 1:]:
                    if any(x in v.lower() for x in ["mr.", "mrs.", "dr."]):
                        lab_faculty = v
                        break

            print(f"{subject} | {subject_faculty} | {lab} | {lab_faculty}")

            # SUBJECT MAP
            if subject and subject_faculty:
                abbr = get_abbreviation(subject)
                subject_data["subjects"].setdefault(abbr, []).append(subject_faculty)

            # LAB MAP
            if lab and lab_faculty:

                lab_abbr = get_abbreviation(lab)

                if "lab" in lab.lower():
                    if not lab_abbr.endswith("L"):
                        lab_abbr += "L"

                if "project" in lab.lower():
                    lab_abbr = "MP"

                for f in lab_faculty.split("/"):
                    subject_data["labs"].setdefault(lab_abbr, []).append(f.strip())

    print("\n📦 JSON DATA:\n")
    print(json.dumps(subject_data, indent=4))

    # ======================
    # ASSIGN FACULTY
    # ======================
    for item in structured:

        subject = item["subject"]
        parts = re.split(r'[/,]', subject)

        faculty_list = []

        for part in parts:

            part = part.strip()

            # ✅ ONLY SPECIAL CASE
            if part == "L":
                abbr = "L"

            else:
                is_lab = "lab" in part.lower()
                is_project = "project" in part.lower()

                clean_part = re.sub(r'lab', '', part, flags=re.IGNORECASE)
                clean_part = re.sub(r'project', '', clean_part, flags=re.IGNORECASE)

                abbr = get_abbreviation(clean_part)

                if is_lab and not abbr.endswith("L"):
                    abbr += "L"

                if is_project:
                    abbr = "MP"

            # MAPPING
            if abbr in subject_data["subjects"]:
                faculty_list.extend(subject_data["subjects"][abbr])

            if abbr in subject_data["labs"]:
                faculty_list.extend(subject_data["labs"][abbr])

        item["faculty"] = " / ".join(sorted(set(faculty_list)))

    # ======================
    # FINAL OUTPUT
    # ======================
    print("\n🎯 FINAL OUTPUT:")
    for r in structured[:10]:
        print(r)

    return pd.DataFrame(structured)