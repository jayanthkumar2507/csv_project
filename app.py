import os
import json
from flask import Flask, render_template, request
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
from PyPDF2 import PdfReader

app = Flask(__name__)

# ================= ENV VARIABLES =================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")

if not SPREADSHEET_ID:
    raise RuntimeError("SPREADSHEET_ID not set")

if not SERVICE_ACCOUNT_JSON:
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON not set")

# ================= GROQ CLIENT (NO STREAMING) =================
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

    # ---- SAFE PDF READ ----
    resume_text = ""
    reader = PdfReader(file)

    for page in reader.pages:
        text = page.extract_text()
        if text:
            resume_text += text + "\n"

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

    # ---- NON-STREAMING CALL (CRITICAL FIX) ----
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        stream=False   # 🔥 THIS FIXES YOUR ERROR
    )

    result = response.choices[0].message.content

    # ---- SAVE TO SHEET (SAFE) ----
    try:
        sheet.append_row([file.filename, result[:40000]])
    except Exception:
        pass

    return render_template("result.html", result=result)

# ================= MAIN =================
if __name__ == "__main__":
    app.run()