import os
import json
import fitz  # PyMuPDF

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

import gspread
from google.oauth2.service_account import Credentials

from groq import Groq


# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ---------------- GROQ CLIENT ----------------
groq_client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)


# ---------------- GOOGLE SHEETS (SAFE MODE) ----------------
sheet = None

try:
    service_account_info = json.loads(
        os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    )

    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(
        os.environ.get("SPREADSHEET_ID")
    ).sheet1

except Exception as e:
    print("⚠ Google Sheets disabled:", e)


# ---------------- PDF TEXT EXTRACTOR ----------------
def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    return text.strip()


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("upload.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return "No file uploaded"

    file = request.files["resume"]
    if file.filename == "":
        return "No selected file"

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    resume_text = extract_text_from_pdf(file_path)
    resume_text = resume_text[:6000] if resume_text else "Empty resume"

    prompt = f"""
Analyze the resume and provide:

1. Strengths
2. Weaknesses
3. Career suggestions
4. Internship recommendations

Resume:
{resume_text}
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700
    )

    result = response.choices[0].message.content

    # ---- SAFE GOOGLE SHEET WRITE ----
    if sheet:
        try:
            sheet.append_row([filename, result[:4000]])
        except Exception as e:
            print("⚠ Sheet write failed:", e)

    return render_template("result.html", result=result)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)