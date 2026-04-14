import pandas as pd
import re


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


def fallback_abbr(text):
    words = re.findall(r'[A-Za-z]+', text)
    return "".join([w[0].upper() for w in words])


def clean_text(text):
    return re.sub(r'\(.*?\)', '', str(text)).strip()


def normalize_time(t):
    return str(t).replace(" ", "")


def normalize_lab_abbr(abbr, faculty_map):
    if abbr in faculty_map:
        return abbr

    # reduce (OSMP → OS)
    for i in range(len(abbr), 1, -1):
        short = abbr[:i]
        if short in faculty_map:
            return short

    return abbr


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
    # EXTRACTION
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
    # FACULTY MAP (THEORY + LAB)
    # ======================
    faculty_map = {}

    print("\n📘 SUBJECT + LAB ABBREVIATIONS:")

    for i in range(len(df)):

        row = [str(x).strip() for x in df.iloc[i]]

        # ---------- THEORY ----------
        if len(row) >= 2 and row[0] and row[1]:

            subject = clean_text(row[0])
            faculty = row[1]

            if subject.lower() not in ["name of the subject", ""]:

                abbr = get_abbreviation(subject)

                if not abbr:
                    abbr = fallback_abbr(subject)

                faculty_map[abbr] = faculty
                print(f"{abbr} → {subject}")

                faculty_map[abbr + "L"] = faculty
                print(f"{abbr+'L'} → {subject} (LAB)")

        # ---------- LAB ----------
        if len(row) >= 4 and row[2] and row[3]:

            lab_subject = clean_text(row[2])
            lab_faculty = row[3]

            if lab_subject.lower() not in ["name of the lab", ""]:

                abbr = get_abbreviation(lab_subject)

                if not abbr:
                    abbr = fallback_abbr(lab_subject)

                faculty_map[abbr] = lab_faculty
                print(f"{abbr} → {lab_subject}")

                faculty_map[abbr + "L"] = lab_faculty
                print(f"{abbr+'L'} → {lab_subject} (LAB)")

    # ======================
    # ASSIGN FACULTY
    # ======================
    for item in structured:

        subject = item["subject"]
        parts = re.split(r'[/,]', subject)

        faculty_list = []

        print(f"\n📗 Processing Subject: {subject}")

        for part in parts:

            original = part
            is_lab = "lab" in part.lower()

            if is_lab:
                part = re.sub(r'lab', '', part, flags=re.IGNORECASE)

            abbr = get_abbreviation(part)

            if not abbr:
                abbr = fallback_abbr(part)

            match_abbr = abbr
            if is_lab:
                match_abbr = normalize_lab_abbr(abbr, faculty_map)

            print(f"   {original} → {abbr} (matched as {match_abbr})")

            if match_abbr in faculty_map:
                names = faculty_map[match_abbr]

                for n in re.split(r'[/,]', names):
                    faculty_list.append(n.strip())

        item["faculty"] = " / ".join(sorted(set(faculty_list)))

    print("\n🎯 FINAL OUTPUT:")
    for r in structured[:10]:
        print(r)

    return pd.DataFrame(structured)