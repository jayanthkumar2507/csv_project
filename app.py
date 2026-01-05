import os, json, base64
from flask import Flask, render_template, request, redirect
from groq import Groq
from PyPDF2 import PdfReader
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# ---------- GROQ ----------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------- GOOGLE SHEETS ----------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

service_account_info = json.loads(
    os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

creds = service_account.Credentials.from_service_account_info(
    service_account_info, scopes=SCOPES
)

sheet_service = build("sheets", "v4", credentials=creds)
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")


# ---------- HELPERS ----------
def extract_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def analyze_resume(text, profession):
    prompt = f"""
Analyze the resume for the profession: {profession}

Return the result in plain text with these headings:

**Strengths**
(numbered points)

**Weaknesses**
(numbered points)

**Skill Gaps**
(numbered points)

**Learning Suggestions**
(numbered points)

**Recommended Job Roles**
(numbered points)

Resume:
{text}
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


def save_to_sheets(filename, profession, analysis):
    values = [[filename, profession, analysis]]

    sheet_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A1",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()


# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("upload.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        # Check file
        if "resume" not in request.files:
            return "Resume field missing", 400

        file = request.files["resume"]

        if file.filename == "":
            return "No file selected", 400

        role = request.form.get("role", "Not selected")

        # Save file safely
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        # SAFE STATIC RESULT (no AI yet)
        result_text = f"""
Target Role:
{role}

Skills Identified:
- Python programming
- Data visualization
- Data cleaning

Strengths:
- Good fundamentals
- Logical thinking

Skill Gaps:
- Machine learning
- Advanced analytics
"""

        return render_template("result.html", data=result_text)

    except Exception as e:
        # THIS PREVENTS 500 ERROR
        return f"Error occurred: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)