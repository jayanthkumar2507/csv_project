import os
import json
import fitz
import gspread
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from groq import Groq
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ---------------- CONFIG ----------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

groq_client = Groq(api_key=GROQ_API_KEY)

# ---------- GOOGLE SHEETS ----------
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# -------- PDF TEXT EXTRACTOR ----------
def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    return text.strip()

# --------------- ROUTES ----------------
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

    if not resume_text:
        resume_text = "Resume content could not be extracted."

    resume_text = resume_text[:6000]

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
        max_tokens=700,
        stream=False
    )

    result = response.choices[0].message.content

    # -------- SAVE TO GOOGLE SHEET --------
    try:
        sheet.append_row([filename, result[:40000]])
    except Exception as e:
        print("Sheet error:", e)

    return render_template("result.html", result=result)

# ------------ LOCAL RUN ---------------
if __name__ == "__main__":
    app.run(debug=True)