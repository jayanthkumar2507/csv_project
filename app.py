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
    try:
        file = request.files.get("resume")
        if not file:
            return "No file uploaded", 400

        # ---- extract text ----
        resume_text = extract_text(file)  # whatever function you use

        if not resume_text.strip():
            return "Resume text could not be extracted", 400

        resume_text = resume_text[:6000]

        # ---- GROQ CALL ----
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": resume_text}],
            max_tokens=700,
            stream=False
        )

        result = response.choices[0].message.content

        # ---- GOOGLE SHEET ----
        try:
            sheet.append_row([file.filename, result[:40000]])
        except Exception as e:
            print("Sheet error:", e)

        return render_template("result.html", result=result)

    except Exception as e:
        print("ANALYZE ERROR:", e)
        return f"Internal Error: {e}", 500
# ================= MAIN =================
if __name__ == "__main__":
    app.run()