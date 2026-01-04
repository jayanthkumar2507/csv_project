import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from groq import Groq
from dotenv import load_dotenv

# ---------------- CONFIG ----------------
load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# ---------------- PDF TEXT EXTRACTOR ----------------
def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    return text.strip()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("upload.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return "No file uploaded"

    file = request.files["resume"]
    if file.filename == "":
        return "No selected file"

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    resume_text = extract_text_from_pdf(file_path)

    if not resume_text:
        resume_text = "Resume content could not be extracted."

    resume_text = resume_text[:6000]  # safety limit

    prompt = f"""
Analyze the resume and provide:

1. Strengths
2. Weaknesses
3. Career suggestions
4. Internship recommendations

Resume:
{resume_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700
    )

    result = response.choices[0].message.content

    return render_template(
        "result.html",
        filename=filename,
        result=result
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)