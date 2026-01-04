import os, json
from flask import Flask, render_template, request
from groq import Groq
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import PyPDF2

load_dotenv()
app = Flask(__name__)

# ---------- GROQ ----------
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------- GOOGLE SHEETS ----------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
gs = gspread.authorize(creds)
sheet = gs.open("Resume_Analysis_Data").sheet1
# ----------------------------------

def extract_text(pdf):
    reader = PyPDF2.PdfReader(pdf)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text

@app.route("/")
def upload():
    return render_template("upload.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    resume_text = extract_text(request.files["resume"])
    profession = request.form.get("profession")

    prompt = f"""
You are an expert resume evaluator for STUDENT / INTERN level candidates.

Target Profession: {profession}

Return ONLY valid JSON. Do NOT include score.

Ensure weaknesses are REAL skill-based weaknesses.

Format:
{{
  "target_role": "{profession}",
  "skills_identified": [],
  "strengths": [],
  "weaknesses": [],
  "skill_gaps": [],
  "learning_suggestions": [],
  "tools_recommended": [],
  "internship_recommendations": []
}}

Resume:
{resume_text}
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    raw = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except:
        data = {
            "target_role": profession,
            "skills_identified": ["Python"],
            "strengths": ["Basic programming knowledge"],
            "weaknesses": [
                "Limited hands-on project experience",
                "Lack of real-world industry exposure"
            ],
            "skill_gaps": ["Advanced concepts"],
            "learning_suggestions": ["Practice projects"],
            "tools_recommended": ["Git", "VS Code"],
            "internship_recommendations": [f"{profession} Intern"]
        }

    # Save to Google Sheets
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data["target_role"],
        ", ".join(data["skills_identified"]),
        ", ".join(data["weaknesses"]),
        ", ".join(data["internship_recommendations"])
    ])

    return render_template("result.html", data=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)