import io
import os
import sys
import time
import pandas as pd
from werkzeug.utils import secure_filename
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_file
)

sys.path.insert(0, os.path.dirname(__file__))

from database.database import save_dataframe
from modules.iqac.processor       import process_iqac
from modules.committees.processor import process_committees
from modules.timetable.processor  import process_timetable
from modules.iqac.excel_generator import generate_iqac_excel

app = Flask(__name__)
app.secret_key = "sdp-secret"

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXT = {"pdf", "docx", "doc", "xlsx", "xls"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

_PREVIEW_STORE = {}

MODULE_PROCESSORS = {
    "iqac": process_iqac,
    "committees": process_committees,
    "timetable": process_timetable,
}

PREVIEW_TEMPLATES = {
    "iqac": "preview_iqac.html",
    "committees": "preview_committees.html",
    "timetable": "preview_timetable.html",
}


# ==========================
# HELPERS
# ==========================
def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def _session_key():
    if "uid" not in session:
        session["uid"] = os.urandom(8).hex()
    return session["uid"]


def _store_df(df):
    _PREVIEW_STORE[_session_key()] = df


def _load_df():
    return _PREVIEW_STORE.get(_session_key())


def _df_to_excel_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()


# ==========================
# ROUTES
# ==========================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/module", methods=["GET", "POST"])
def module():

    if request.method == "POST":
        file = request.files.get("file")

        if not file or not file.filename:
            return "❌ No file selected"

        if not _allowed(file.filename):
            return "❌ Unsupported file type"

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        session["uploaded_file"] = file_path
        session["original_name"] = file.filename

    if "uploaded_file" not in session:
        return redirect(url_for("index"))

    return render_template("module.html", file_path=session.get("original_name"))


# ==========================
# PROCESS (PREVIEW ONLY)
# ==========================
@app.route("/process", methods=["POST"])
def process():

    module = request.form.get("module", "").lower()
    file_path = session.get("uploaded_file")

    if not file_path:
        return "❌ File path missing"

    if module not in MODULE_PROCESSORS:
        return f"❌ Invalid module: {module}"

    try:
        # ✅ ONLY EXTRACT RAW DATA
        df = MODULE_PROCESSORS[module](file_path)

    except Exception as e:
        return f"<h2>Error:</h2><pre>{e}</pre>"

    if df is None or df.empty:
        return "❌ No data extracted"

    # ✅ STORE RAW DATA (IMPORTANT)
    _store_df(df)
    session["current_module"] = module

    rows = df.to_dict(orient="records")
    columns = list(df.columns)

    return render_template(
        PREVIEW_TEMPLATES[module],
        rows=rows,
        columns=columns,
        module=module
    )


# ==========================
# FINAL (SAVE + DOWNLOAD)
# ==========================
@app.route("/final", methods=["POST"])
def final():

    df = _load_df()
    module = session.get("current_module", "data")

    if df is None or df.empty:
        return "❌ No data available"

    table_name = f"{module}_{int(time.time())}"

    try:
        # ✅ SAVE RAW DATA TO DATABASE
        save_dataframe(df, table_name)
        print(f"✅ Saved to DB: {table_name}")

        # ==========================
        # IQAC TEMPLATE GENERATION
        # ==========================
        if module == "iqac":

            template_path = "modules/iqac/template.xlsx"
            output_path = f"{table_name}.xlsx"

            generate_iqac_excel(df, template_path, output_path)

            return send_file(output_path, as_attachment=True)

        # ==========================
        # OTHER MODULES (NORMAL EXCEL)
        # ==========================
        else:
            excel_bytes = _df_to_excel_bytes(df)

            return send_file(
                io.BytesIO(excel_bytes),
                as_attachment=True,
                download_name=f"{table_name}.xlsx",
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        return f"❌ Error: {e}"


# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    app.run(debug=True,use_reloader=False)