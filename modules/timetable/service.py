import time
from .extractor import extract_timetable


def handle_timetable(file_path):

    print("🚀 Starting Timetable Processing...")

    # 🔥 Step 1: Extract structured data
    df = extract_timetable(file_path)

    if df.empty:
        raise Exception("❌ No timetable data extracted. Check file format.")

    # 🔥 Step 2: Generate unique table name
    table_name = f"timetable_{int(time.time())}"

    print("✅ Timetable processed successfully")
    print("📊 Rows extracted:", len(df))

    return df, table_name