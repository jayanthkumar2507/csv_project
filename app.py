import os
import json
from flask import Flask, render_template, request
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
from PyPDF2 import PdfReader

app = Flask(__name__)

# ================= ENV =================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")
if not SPREADSHEET_ID:
    raise RuntimeError("SPREADSHEET_ID not set")
if not SERVICE_ACCOUNT_JSON:
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON not set")

# ================= GROQ =================
groq_client = Groq(api_key=GROQ_API_KEY)

# ================= GOOGLE SHEETS =================
service_account_info = json.loads(SERVICE_ACCOUNT_JSON)

credentials = Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# ================= ROUTES =================
@app.route("/")
def upload():
    return render_template("upload.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files["resume"]

    # ---- SAFE PDF EXTRACTION ----
    reader = PdfReader(file)
    resume_text = ""

    for page in reader.pages[:5]:   # 🔥 LIMIT PAGES
        text = page.extract_text()
        if text:
            resume_text += text + "\n"

    resume_text = resume_text[:6000]  # 🔥 LIMIT SIZE

    if not resume_text.strip():
        resume_text = "Resume content could not be extracted."

    prompt = f"""
Analyze the resume and give:
1. Strengths
2. Weaknesses
3. Career suggestions
4. Internship recommendations

Resume:
{resume_text}
"""

    # ---- HARD LIMITED RESPONSE ----
    response = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700,     # 🔥 CRITICAL
        stream=False
    )

    result = response.choices[0].message.content

    # ---- SAFE SHEET WRITE ----
    try:
        sheet.append_row([file.filename, result[:40000]])
    except Exception:
        pass

    return render_template("result.html", result=result)

# ================= MAIN =================
if __name__ == "__main__":
    app.run()