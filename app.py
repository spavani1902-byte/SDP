from flask import Flask, request, render_template
import os
import pandas as pd
import oracledb

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# 🔹 Oracle DB connection
def get_db_connection():
    return oracledb.connect(
        user="system",        # 🔴 change
        password="password",    # 🔴 change
        dsn="localhost:1521/XEPDB1"       # default Oracle XE
    )


# 🔹 Home page
@app.route("/")
def home():
    return render_template("index.html", message=None)


# 🔹 Upload file
@app.route("/upload", methods=["POST"])
def upload_file():

    pdf = request.files.get("pdf_file")
    word = request.files.get("word_file")
    excel = request.files.get("excel_file")

    if pdf and pdf.filename != "":
        if not pdf.filename.endswith(".pdf"):
            return render_template("index.html", message="Upload correct PDF file")
        file = pdf

    elif word and word.filename != "":
        if not (word.filename.endswith(".doc") or word.filename.endswith(".docx")):
            return render_template("index.html", message="Upload correct Word file")
        file = word

    elif excel and excel.filename != "":
        if not excel.filename.endswith(".xlsx"):
            return render_template("index.html", message="Upload correct Excel file")
        file = excel

    else:
        return render_template("index.html", message="Please upload a file")

    # Save file
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    return render_template("structure.html")


# 🔹 Structure page
@app.route("/structure")
def structure():
    return render_template("structure.html")


# 🔹 Get counts → go to headings page
@app.route("/headings", methods=["POST"])
def headings():

    main_count = int(request.form.get("main_count"))
    sub_count = int(request.form.get("sub_count"))

    return render_template(
        "headings.html",
        main_count=main_count,
        sub_count=sub_count
    )


# 🔹 Store headings in Oracle DB
@app.route("/submit_headings", methods=["POST"])
def submit_headings():

    data = request.form.to_dict()

    conn = get_db_connection()
    cursor = conn.cursor()

    main_headings = []
    sub_headings = []

    for key, value in data.items():
        if "main_heading" in key:
            main_headings.append(value)
            cursor.execute(
                "INSERT INTO HEADINGS (type, name) VALUES (:1, :2)",
                ("main", value)
            )

        elif "sub_heading" in key:
            sub_headings.append(value)
            cursor.execute(
                "INSERT INTO HEADINGS (type, name) VALUES (:1, :2)",
                ("sub", value)
            )

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        main_headings=main_headings,
        sub_headings=sub_headings
    )


# 🔹 Run app
if __name__ == "__main__":
    app.run(debug=True)