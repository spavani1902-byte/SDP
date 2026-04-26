"""
service.py
----------
Flask application. Handles file upload, preview, SQLite save, and Excel download.
All heavy lifting is delegated to processor.py.
"""

import io
import os
import sqlite3
import tempfile

import pandas as pd
from flask import (
    Flask,
    jsonify,
    request,
    send_file,
)

from processor import process_file

app = Flask(__name__)

DB_PATH = os.environ.get("SDP_DB", "data.db")
UPLOAD_FOLDER = tempfile.gettempdir()

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "xlsx", "xls"}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_temp(file_storage) -> str:
    """Save an uploaded FileStorage object to a temp file; return its path."""
    ext = os.path.splitext(file_storage.filename)[1]
    fd, tmp_path = tempfile.mkstemp(suffix=ext, dir=UPLOAD_FOLDER)
    os.close(fd)
    file_storage.save(tmp_path)
    return tmp_path


def _df_to_sqlite(df: pd.DataFrame, table_name: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        df.to_sql(table_name, conn, if_exists="append", index=False)
        conn.commit()
    finally:
        conn.close()


def _df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Extracted Data")
    return buf.getvalue()


def _error(msg: str, code: int = 400):
    return jsonify({"success": False, "error": msg}), code


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/extract", methods=["POST"])
def extract():
    """
    POST /extract
    Form-data fields:
      - file   : the document to process
      - module : one of iqac | committees | timetable
    
    Returns JSON:
      { "success": true, "rows": [...], "columns": [...] }
    """
    if "file" not in request.files:
        return _error("No file provided.")

    file = request.files["file"]
    module = request.form.get("module", "").strip().lower()

    if not file.filename:
        return _error("Empty filename.")
    if not _allowed(file.filename):
        return _error(f"Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}")
    if not module:
        return _error("'module' field is required (iqac | committees | timetable).")

    tmp_path = _save_temp(file)
    try:
        df = process_file(tmp_path, module)
    except ValueError as exc:
        return _error(str(exc))
    except Exception as exc:
        return _error(f"Processing error: {exc}", 500)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return jsonify({
        "success": True,
        "columns": list(df.columns),
        "rows":    df.where(pd.notnull(df), None).to_dict(orient="records"),
    })


@app.route("/save", methods=["POST"])
def save():
    """
    POST /save
    JSON body:
      { "module": "iqac", "rows": [...] }

    Saves rows into SQLite table named after the module.
    """
    body = request.get_json(force=True, silent=True)
    if not body:
        return _error("JSON body required.")

    module = body.get("module", "").strip().lower()
    rows   = body.get("rows", [])

    if not module:
        return _error("'module' field is required.")
    if not rows:
        return _error("'rows' list is empty.")

    table_name = module.replace(" ", "_")
    df = pd.DataFrame(rows)

    try:
        _df_to_sqlite(df, table_name)
    except Exception as exc:
        return _error(f"Database error: {exc}", 500)

    return jsonify({"success": True, "saved": len(df), "table": table_name})


@app.route("/download", methods=["POST"])
def download():
    """
    POST /download
    JSON body:
      { "module": "iqac", "rows": [...] }

    Returns an .xlsx file for download.
    """
    body = request.get_json(force=True, silent=True)
    if not body:
        return _error("JSON body required.")

    module = body.get("module", "").strip().lower()
    rows   = body.get("rows", [])

    if not rows:
        return _error("'rows' list is empty.")

    df = pd.DataFrame(rows)
    excel_bytes = _df_to_excel_bytes(df)
    safe_name = module.replace(" ", "_") or "extracted"

    return send_file(
        io.BytesIO(excel_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"{safe_name}_data.xlsx",
    )


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)