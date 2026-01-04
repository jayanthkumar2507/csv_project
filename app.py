import os, json
from flask import Flask, render_template, request, redirect
from groq import Groq
from PyPDF2 import PdfReader
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# -------- GROQ --------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# -------- GOOGLE SHEETS --------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")

creds = service_account.Credentials.from_service_account_file(
    "service_account.json", scopes=SCOPES
)

sheet_service = build("sheets", "v4", credentials=creds)

# -------- HELPERS --------
def extract_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def analyze_resume(text, profession):
    prompt = f"""
You are an expert resume reviewer.

Analyze the resume for the target profession:
{profession}

Rules:
- strengths → positive skills or qualities
- weaknesses → soft-skill or experience limitations
- skill_gaps → missing technical skills (nouns only)
- learning_suggestions → action steps (verbs like Learn, Build, Practice)
- tools → software or technologies only
- internships → realistic internship roles

Do NOT repeat ideas across sections.
Return ONLY valid JSON.

JSON FORMAT:
{{
  "strengths": [],
  "weaknesses": [],
  "skill_gaps": [],
  "learning_suggestions": [],
  "tools": [],
  "internships": []
}}

Resume:
{text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.15
    )

    return json.loads(response.choices[0].message.content)


def safe_join(items):
    cleaned = []
    for i in items:
        if isinstance(i, dict):
            cleaned.append(str(list(i.values())[0]))
        else:
            cleaned.append(str(i))
    return " | ".join(cleaned)


def save_to_sheets(filename, profession, result):
    values = [[
        filename,
        profession,
        safe_join(result["strengths"]),
        safe_join(result["weaknesses"]),
        safe_join(result["skill_gaps"]),
        safe_join(result["learning_suggestions"]),
        safe_join(result["tools"]),
        safe_join(result["internships"])
    ]]

    sheet_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A1",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()# -------- ROUTES --------
@app.route("/")
def home():
    return render_template("upload.html")


@app.route("/analyze", methods=["POST", "GET"])
def analyze():
    if request.method == "GET":
        return redirect("/")

    file = request.files["resume"]
    profession = request.form.get("profession")

    text = extract_text(file)
    result = analyze_resume(text, profession)

    save_to_sheets(file.filename, profession, result)

    return render_template("result.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)