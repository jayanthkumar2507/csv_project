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

# ================= GROQ CLIENT =================
groq_client = Groq(api_key=GROQ_API_KEY)

# ================= GOOGLE SHEETS =================
service_account_info = json.loads(SERVICE_ACCOUNT_JSON)

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(
    service_account_info, scopes=scopes
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

    reader = PdfReader(file)
    resume_text = ""
    for page in reader.pages:
        resume_text += page.extract_text()

    prompt = f"""
Analyze this resume and return:
1. Strengths
2. Weaknesses
3. Suggested career roles
4. Internship recommendations

Resume:
{resume_text}
"""

    response = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content

    # Save to Google Sheet
    sheet.append_row([file.filename, result])

    return render_template("result.html", result=result)

# ================= MAIN =================
if __name__ == "__main__":
    app.run()