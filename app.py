import sys
import os
import pandas as pd
from flask import Flask, request, render_template, send_file

# 🔥 Fix import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ✅ IMPORT SERVICES
from modules.iqac.service import handle_iqac
from modules.committees.service import handle_committees

# ✅ DATABASE
from database.database import get_connection

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# 🔁 Temporary storage (for preview → confirm)
TEMP_DATA = {}


# 🏠 HOME PAGE
@app.route('/')
def index():
    return render_template('index.html')


# 📤 STEP 1: Upload file → go to module selection
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
        return "No file uploaded"

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    return render_template("module.html", file_path=file_path)


@app.route('/process', methods=['POST'])
def process():

    module = request.form.get('module')
    file_path = request.form.get('file_path')

    if not module or not file_path:
        return "Invalid request"

    try:
        # ======================
        # IQAC MODULE
        # ======================
        if module == "iqac":

            parsed, table_name = handle_iqac(file_path)

            # store for confirm
            TEMP_DATA["data"] = parsed
            TEMP_DATA["table_name"] = table_name
            TEMP_DATA["module"] = module
            print("DEBUG PARSED:", parsed[:5])
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

        else:
            return "Invalid module selected"

    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/confirm', methods=['POST'])
def confirm():

    module = TEMP_DATA.get("module")
    table_name = TEMP_DATA.get("table_name")

    if not module:
        return "Session expired"

    # ======================
    # IQAC MODULE
    # ======================
    if module == "iqac":

        from modules.iqac.generator import update_mapping
        import pandas as pd

        parsed = TEMP_DATA["data"]

        # 🔥 1. STORE CLEAN DATA IN DB
        df_db = pd.DataFrame(parsed)

        conn = get_connection()
        df_db.to_sql("iqac_data", conn, if_exists="append", index=False)
        conn.close()

        # 🔥 2. GENERATE TEMPLATE OUTPUT
        output_file = f"{table_name}.xlsx"
        update_mapping(output_file, parsed)

        # ❌ DO NOT use df.to_excel here

        # 🔥 3. DOWNLOAD
        return send_file(output_file, as_attachment=True)

    # ======================
    # COMMITTEES MODULE
    # ======================
    elif module == "committees":

        df = TEMP_DATA["data"]

        # 🔥 STORE IN DB
        conn = get_connection()
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()

        # 🔥 DOWNLOAD
        output_file = f"{table_name}.xlsx"
        df.to_excel(output_file, index=False)

        return send_file(output_file, as_attachment=True)

    else:
        return "Invalid module"


# ▶️ RUN APP
if __name__ == "__main__":
    app.run(debug=True)