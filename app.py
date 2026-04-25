import sys
import os
import pandas as pd
from flask import Flask, request, render_template, send_file

# Fix import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Services (ONLY extraction)
from modules.iqac.service import handle_iqac
from modules.committees.service import handle_committees
from modules.timetable.service import handle_timetable

from database.database import get_connection

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

TEMP_DATA = {}


# ==========================
# HOME PAGE
# ==========================
@app.route('/')
def index():
    return render_template('index.html')


# ==========================
# FILE UPLOAD
# ==========================
@app.route('/module', methods=['POST'])
def module():

    file = request.files.get('file')

    if not file or file.filename == "":
        return "❌ No file uploaded"

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    return render_template("module.html", file_path=file_path)


# ==========================
# PROCESS (PREVIEW ONLY)
# ==========================
@app.route('/process', methods=['POST'])
def process():

    module = request.form.get('module')
    file_path = request.form.get('file_path')

    if not module or not file_path:
        return "❌ Invalid request"

    try:
        # 🔄 Convert Word → Excel
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".docx":
            from word.converter import convert_word_to_excel
            file_path = convert_word_to_excel(file_path)

        # ======================
        # MODULE HANDLING
        # ======================
        if module == "iqac":
            df, table_name = handle_iqac(file_path)
            template = "preview_iqac.html"

        elif module == "committees":
            df, table_name = handle_committees(file_path)
            template = "preview_committees.html"

        elif module == "timetable":
            df, table_name = handle_timetable(file_path)
            template = "preview_timetable.html"

        else:
            return "❌ Invalid module selected"

        # 🔥 Ensure DataFrame
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

        if df.empty:
            return "❌ No data extracted"

        # 🔥 STORE EXACT DATAFRAME (IMPORTANT CHANGE)
        TEMP_DATA["df"] = df
        TEMP_DATA["table_name"] = table_name
        TEMP_DATA["module"] = module

        print("📊 PREVIEW DATA:")
        print(df.head())

        # 🔥 Convert for UI only
        data = df.to_dict(orient='records')

        return render_template(
            template,
            data=data,
            table_name=table_name,
            module=module,
            file_path=file_path
        )

    except Exception as e:
        return f"❌ Error: {e}"


# ==========================
# CONFIRM → STORE + DOWNLOAD
# ==========================
@app.route('/confirm', methods=['POST'])
def confirm():

    df = TEMP_DATA.get("df")
    table_name = TEMP_DATA.get("table_name")

    if df is None or table_name is None:
        return "❌ Session expired"

    if df.empty:
        return "❌ No data to store"

    try:
        print("📊 STORING DATA:")
        print(df.head())

        # 🔥 STORE EXACT PREVIEW DATA
        conn = get_connection()

        df.to_sql(table_name, conn, if_exists="replace", index=False)

        conn.commit()   # 🔥 IMPORTANT
        conn.close()

        print(f"✅ Data stored in DB: {table_name}")

        # 🔥 Download file
        output_file = f"{table_name}.xlsx"
        df.to_excel(output_file, index=False)

        return send_file(output_file, as_attachment=True)

    except Exception as e:
        return f"❌ DB Error: {e}"


# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)