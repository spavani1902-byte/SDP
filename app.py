import sys
import os
import pandas as pd
from flask import Flask, request, render_template, send_file

# Fix import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Services
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
# PROCESS
# ==========================
@app.route('/process', methods=['POST'])
def process():

    module = request.form.get('module')
    file_path = request.form.get('file_path')

    if not module or not file_path:
        return "❌ Invalid request"

    try:
        # 🔥 AUTO Word → Excel
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".docx":
            from word.converter import convert_word_to_excel
            print("📄 Converting Word → Excel...")
            file_path = convert_word_to_excel(file_path)
            print("✅ Converted:", file_path)

        # ======================
        # IQAC
        # ======================
        if module == "iqac":

            parsed, table_name = handle_iqac(file_path)

            TEMP_DATA["data"] = parsed
            TEMP_DATA["table_name"] = table_name
            TEMP_DATA["module"] = module

            return render_template(
                "preview_iqac.html",
                data=parsed,
                table_name=table_name,
                module=module,
                file_path=file_path
            )

        # ======================
        # COMMITTEES
        # ======================
        elif module == "committees":

            df, table_name = handle_committees(file_path)

            TEMP_DATA["data"] = df
            TEMP_DATA["table_name"] = table_name
            TEMP_DATA["module"] = module

            table_html = df.to_html(classes='table table-bordered', index=False)

            return render_template(
                "preview_committees.html",
                table=table_html,
                table_name=table_name,
                module=module,
                file_path=file_path
            )

        # ======================
        # TIMETABLE
        # ======================
        elif module == "timetable":

            df, table_name = handle_timetable(file_path)

            TEMP_DATA["data"] = df
            TEMP_DATA["table_name"] = table_name
            TEMP_DATA["module"] = module

            table_html = df.to_html(classes='table table-bordered', index=False)

            return render_template(
                "preview_timetable.html",
                table=table_html,
                table_name=table_name,
                module=module,
                file_path=file_path
            )

        else:
            return "❌ Invalid module selected"

    except Exception as e:
        raise e


# ==========================
# CONFIRM + DOWNLOAD
# ==========================
@app.route('/confirm', methods=['POST'])
def confirm():

    module = TEMP_DATA.get("module")
    table_name = TEMP_DATA.get("table_name")

    if module is None:
        return "❌ Session expired"

    if module == "iqac":
        parsed = TEMP_DATA["data"]

        from modules.iqac.generator import update_mapping
        import time

        output_file = f"iqac_output_{int(time.time())}.xlsx"
        update_mapping(output_file, parsed)
        df = pd.read_excel(output_file)

    elif module == "committees":
        df = TEMP_DATA["data"]

    elif module == "timetable":
        df = TEMP_DATA["data"]
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

    else:
        return "❌ Unknown module"

    if df is None or df.empty:
        return "❌ No data to store"

    conn = get_connection()
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

    output_file = f"{table_name}.xlsx"
    df.to_excel(output_file, index=False)

    return send_file(output_file, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)