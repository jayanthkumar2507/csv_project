import os, json
from flask import Flask, render_template, request
from groq import Groq
from PyPDF2 import PdfReader
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Groq
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Google Sheets
creds = Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]),
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
sheet_service = build("sheets", "v4", credentials=creds)
SHEET_ID = os.environ["GOOGLE_SHEET_ID"]


@app.route("/")
def upload():
    return render_template("upload.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files["resume"]
    role = request.form.get("role", "Not selected")

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Read PDF
    reader = PdfReader(filepath)
    resume_text = "\n".join([p.extract_text() or "" for p in reader.pages])

    prompt = f"""
Analyze the resume and return ONLY plain text (no **, no markdown):

Target Role
Skills Identified
Strengths
Skill Gaps

Resume:
{resume_text}
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700
    )

    analysis = response.choices[0].message.content

    # Save to Google Sheets
    sheet_service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="A:D",
        valueInputOption="RAW",
        body={
            "values": [[
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                file.filename,
                role,
                analysis
            ]]
        }
    ).execute()

    return render_template("result.html", analysis=analysis)


if __name__ == "__main__":
    app.run(debug=True)