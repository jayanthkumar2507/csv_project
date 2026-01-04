import os
import json
import requests
from flask import Flask, render_template, request
import PyPDF2

import gspread
from google.oauth2.service_account import Credentials

# ---------------- BASIC CONFIG ----------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

# ---------------- ENV VARIABLES ----------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ---------------- GOOGLE SHEETS ----------------
def get_sheet():
    service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)

    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES
    )

    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_ID).sheet1

# ---------------- PDF UTILS ----------------
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text()
    return text.strip()

# ---------------- GROQ (FINAL FIXED VERSION) ----------------
def analyze_with_groq(resume_text):
    if not GROQ_API_KEY:
        raise Exception("GROQ_API_KEY not set")

    # Prevent Groq 400 error (token overflow)
    resume_text = resume_text[:6000]

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert resume analyzer."
            },
            {
                "role": "user",
                "content": f"""
Analyze the resume and respond ONLY with the following sections:

Strengths:
Weaknesses:
Skill Gaps:
Recommended Job Roles:
Internship Suggestions:

Resume:
{resume_text}
"""
            }
        ],
        "temperature": 0.4,
        "max_tokens": 700
    }

    response = requests.post(GROQ_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Groq API Error {response.status_code}: {response.text}")

    return response.json()["choices"][0]["message"]["content"]

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("upload.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        if "resume" not in request.files:
            return "No file uploaded", 400

        file = request.files["resume"]
        if file.filename == "":
            return "Empty file", 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        resume_text = extract_text_from_pdf(file_path)
        if not resume_text:
            return "Unable to extract text from PDF", 400

        analysis = analyze_with_groq(resume_text)

        # Save to Google Sheets (safe, non-blocking)
        try:
            sheet = get_sheet()
            sheet.append_row([file.filename, analysis])
        except Exception as sheet_error:
            print("Google Sheets error:", sheet_error)

        return render_template("result.html", analysis=analysis)

    except Exception as e:
        print("APP ERROR:", e)
        return f"Internal Error: {e}", 500

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()