import os
import json
import fitz  # PyMuPDF
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

# Google Sheets
import gspread
from google.oauth2.service_account import Credentials

# Groq
from groq import Groq

# ------------------ CONFIG ------------------

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ------------------ PDF TEXT EXTRACT ------------------

def extract_text_from_pdf(pdf_path):
    try:
        text = ""
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        return text.strip()
    except Exception:
        return ""

# ------------------ GOOGLE SHEETS (SAFE) ------------------

sheet = None
try:
    service_account_info = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "{}"))
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(os.environ.get("SPREADSHEET_ID")).sheet1
except Exception:
    sheet = None  # app will still work

# ------------------ GROQ CLIENT ------------------

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ------------------ ROUTES ------------------

@app.route("/")
def home():
    return render_template("upload.html")

@app.route("/analyze", methods=["GET", "POST"])
def analyze():

    # 👉 DIRECT OPEN (GET request)
    if request.method == "GET":
        return render_template("result.html", data={
            "strengths": "Upload a resume to analyze strengths.",
            "weaknesses": "Upload a resume to analyze weaknesses.",
            "careers": "Career suggestions will appear here.",
            "internships": "Internship recommendations will appear here."
        })

    # 👉 FORM SUBMISSION (POST request)
    if "resume" not in request.files:
        return "No file uploaded"

    file = request.files["resume"]
    if file.filename == "":
        return "No selected file"

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    resume_text = extract_text_from_pdf(file_path)

    if not resume_text.strip():
        resume_text = "Resume content could not be extracted."

    resume_text = resume_text[:6000]  # safety limit

    prompt = f"""
Analyze the resume and give:
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

    return render_template("result.html", data={
        "strengths": result,
        "weaknesses": "",
        "careers": "",
        "internships": ""
    })# ------------------ RUN ------------------

if __name__ == "__main__":
    app.run(debug=True)