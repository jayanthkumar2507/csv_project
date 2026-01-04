import os
import json
from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq
from PyPDF2 import PdfReader

app = Flask(__name__)

# =========================
# ENV VARIABLES (REQUIRED)
# =========================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")

if not SPREADSHEET_ID:
    raise RuntimeError("SPREADSHEET_ID not set")

if not GOOGLE_SERVICE_ACCOUNT_JSON:
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON not set")


# =========================
# GROQ CLIENT
# =========================
groq_client = Groq(api_key=GROQ_API_KEY)


# =========================
# GOOGLE SHEETS CLIENT
# =========================
def get_gspread_client():
    service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=scopes
    )

    return gspread.authorize(creds)


# =========================
# PDF TEXT EXTRACT
# =========================
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()


# =========================
# AI ANALYSIS
# =========================
def analyze_resume(text):
    prompt = f"""
Analyze the following resume and provide:
1. Strengths
2. Weaknesses
3. Skills
4. Suggested Job Roles
5. Internship Suggestions
6. Learning Recommendations

Resume:
{text}
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


# =========================
# ROUTES
# =========================
@app.route("/", methods=["GET"])
def upload():
    return render_template("upload.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("resume")

    if not file or file.filename == "":
        return "No file uploaded", 400

    resume_text = extract_text_from_pdf(file)
    analysis = analyze_resume(resume_text)

    # Write to Google Sheet
    gc = get_gspread_client()
    sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
    sheet.append_row([file.filename, analysis])

    return render_template(
        "result.html",
        analysis=analysis
    )


# =========================
# RENDER ENTRY POINT
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)