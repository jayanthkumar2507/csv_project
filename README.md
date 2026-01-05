# 📄 Resume Analyzer (Deployed Web Application)

A fully deployed Flask-based web application that analyzes resumes using **Groq AI** and securely stores results in **Google Sheets**.  
Users can upload a PDF resume and instantly receive AI-driven insights.

---

## 🌐 Live Application

🔗 https://csv-project-28.onrender.com
❌ No secrets or credential files are committed to GitHub.

---

## 📊 Google Sheets Integration

- Resume analysis results are appended to a Google Sheet
- Authentication is done using a **Google Service Account**
- Service account credentials are stored securely as a Base64 environment variable
- The Google Sheet is shared with the service account email (Editor access)

---

## 🧠 Application Workflow

1. User uploads a resume (PDF)
2. Resume text is extracted automatically
3. Text is sent to Groq AI for analysis
4. AI-generated insights are displayed to the user
5. Analysis data is stored in Google Sheets

---

## ❌ What This Project Avoids

- No API keys exposed in code
- No `service_account.json` pushed to GitHub
- No cron jobs (not required)
- No hardcoded credentials
- No manual intervention after deployment

---

## 🎯 Project Outcome

This project demonstrates:
- Real-world AI API integration
- Secure cloud deployment practices
- Backend-to-Google API authentication
- Production-ready Flask application design

---

## 👨‍💻 Author

**Jayanth Kumar Mutha**

---

## 📜 License

This project is created for educational and learning purposes.


The application is successfully deployed and running in production.

---

## ✅ Deployment Status

- ✔ Successfully deployed on Render
- ✔ Groq AI integration working
- ✔ Google Sheets integration working
- ✔ Secure environment variable handling
- ✔ No local credential files used
- ✔ Production-ready setup

---

## 🚀 Features

- Upload resume in **PDF format**
- Automatic text extraction from resume
- AI-based resume analysis using **Groq**
- Displays:
  - Strengths
  - Weaknesses
  - Skill gaps
  - Recommended job roles
  - Internship suggestions
- Stores results in **Google Sheets**
- Clean and simple user interface
- Secure backend configuration

---

## 🛠️ Tech Stack

- **Python**
- **Flask**
- **Groq API**
- **Google Sheets API**
- **HTML & CSS**
- **Gunicorn**
- **Render (Cloud Deployment)**

---

## 📁 Project Structure

csv_project/
│
├── app.py
├── requirements.txt
├── templates/
│ ├── upload.html
│ └── result.html
├── static/
│ └── style.css
├── uploads/
├── .gitignore
└── README.md

---

## 🔐 Environment Variables (Production)

All sensitive data is handled using environment variables on the deployment platform.


