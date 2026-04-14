import sys
import os
import pandas as pd
from flask import Flask, request, render_template, send_file

# 🔥 Fix import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ✅ IMPORT SERVICES
from modules.iqac.service import handle_iqac
from modules.committees.service import handle_committees
from modules.timetable.service import handle_timetable

# ✅ DATABASE
from database.database import get_connection

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# 🔁 Temporary storage (for preview → confirm)
TEMP_DATA = {}


# ==========================
# 🏠 HOME PAGE
# ==========================
@app.route('/')
def index():
    return render_template('index.html')


# ==========================
# 📤 STEP 1: FILE UPLOAD
# ==========================
@app.route('/module', methods=['POST'])
def module():

    file = None

    # Handle multiple inputs
    if 'excel_file' in request.files and request.files['excel_file'].filename != "":
        file = request.files['excel_file']

    elif 'pdf_file' in request.files and request.files['pdf_file'].filename != "":
        file = request.files['pdf_file']

    elif 'word_file' in request.files and request.files['word_file'].filename != "":
        file = request.files['word_file']

    if not file:
        return "❌ No file uploaded"

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    return render_template("module.html", file_path=file_path)


# ==========================
# ⚙ STEP 2: PROCESS MODULE
# ==========================
@app.route('/process', methods=['POST'])
def process():

    module = request.form.get('module')
    file_path = request.form.get('file_path')

    if not module or not file_path:
        return "❌ Invalid request"

    try:

        # ======================
        # IQAC MODULE
        # ======================
        if module == "iqac":

            parsed, table_name = handle_iqac(file_path)

            TEMP_DATA["data"] = parsed
            TEMP_DATA["table_name"] = table_name
            TEMP_DATA["module"] = module

            return render_template(
                "preview_iqac.html",
                data=parsed,
                table_name=table_name
            )

        # ======================
        # COMMITTEES MODULE
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
                table_name=table_name
            )

        # ======================
        # TIMETABLE MODULE
        # ======================
        elif module == "timetable":

            df, table_name = handle_timetable(file_path)

            TEMP_DATA["data"] = df
            TEMP_DATA["table_name"] = table_name
            TEMP_DATA["module"] = module

            # convert to html
            table_html = df.to_html(classes='table table-bordered', index=False)

            return render_template(
                "preview_timetable.html",
                table=table_html,
                table_name=table_name
            )

        else:
            return "❌ Invalid module selected"

    except Exception as e:
        return f"❌ Error: {str(e)}"


# ==========================
# ✅ STEP 3: CONFIRM + SAVE
# ==========================
@app.route('/confirm', methods=['POST'])
def confirm():

    module = TEMP_DATA.get("module")
    table_name = TEMP_DATA.get("table_name")

    if module is None:
        return "❌ Session expired"

    # ======================
    # IQAC
    # ======================
    if module == "iqac":

        parsed = TEMP_DATA["data"]

        from modules.iqac.generator import update_mapping
        import time

        output_file = f"iqac_output_{int(time.time())}.xlsx"
        update_mapping(output_file, parsed)

        df = pd.read_excel(output_file)

    # ======================
    # COMMITTEES
    # ======================
    elif module == "committees":

        df = TEMP_DATA["data"]

    # ======================
    # TIMETABLE
    # ======================
    elif module == "timetable":

        df = TEMP_DATA["data"]

        # 🔥 IMPORTANT FIX
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

    else:
        return "❌ Unknown module"

    # ======================
    # VALIDATE DATA
    # ======================
    if df is None or df.empty:
        return "❌ No data to store"

    print("✅ Saving to DB:")
    print(df.head())

    # ======================
    # SAVE TO DATABASE
    # ======================
    conn = get_connection()
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

    print(f"✅ Stored in DB table: {table_name}")

    # ======================
    # DOWNLOAD FILE
    # ======================
    output_file = f"{table_name}.xlsx"
    df.to_excel(output_file, index=False)

    return send_file(output_file, as_attachment=True)


# ==========================
# ▶ RUN APP
# ==========================
if __name__ == "__main__":
    app.run(debug=True)