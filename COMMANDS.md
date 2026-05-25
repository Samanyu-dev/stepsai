# 🛠️ Steps AI Mock Interview Platform - Useful Commands

This document lists all standard operational, testing, and Git commands for managing, running, and validating this project.

---

## 📦 1. Local Environment & Installation

### Setup Virtual Environment
Create a lightweight, isolated virtual environment to manage dependencies:
```bash
python3 -m venv venv
```

### Activate Virtual Environment
- **Mac / Linux**:
  ```bash
  source venv/bin/activate
  ```
- **Windows (Command Prompt)**:
  ```cmd
  venv\Scripts\activate.bat
  ```
- **Windows (PowerShell)**:
  ```powershell
  venv\Scripts\Activate.ps1
  ```

### Install Dependencies
Upgrade pip and install the complete operational free stack packages:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 2. Running the Application

### Start Development Server (Hot-Reload)
Launches the FastAPI application context with active file changes monitoring:
```bash
uvicorn app.main:app --reload
```
By default, the server will start listening at `http://127.0.0.1:8000`.

### Custom Port & Host
Bind the server to custom ports or network interfaces:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 3. Automated Testing Suite

We use `pytest` for validation and regressions checks. Make sure your virtual environment is **active** when executing tests.

### Run All Tests
```bash
pytest
```

### Run Tests with Verbosity (Shows individual test names)
```bash
pytest -v
```

### Run Specific Test Modules
- Run only health endpoint checks:
  ```bash
  pytest app/tests/test_health.py
  ```
- Run only resume uploading and parsing checks:
  ```bash
  pytest app/tests/test_resume.py
  ```
- Run only streaming conversational engine checks:
  ```bash
  pytest app/tests/test_interview.py
  ```

---

## 📡 4. Testing Endpoints via Terminal (cURL)

Make sure your FastAPI server is running (`uvicorn app.main:app --reload`) before executing these commands:

### A. Health Endpoint Check
```bash
curl http://127.0.0.1:8000/api/v1/health
```

### B. Upload Resume (PDF or DOCX)
Replaces `/path/to/resume.pdf` with the actual absolute path to your test document file:
```bash
curl -X POST -F "file=@/path/to/resume.pdf" http://127.0.0.1:8000/api/v1/resume/upload
```
*Tip: Keep the returned `"session_id"` to use in subsequent interview endpoints.*

### C. Retrieve Parsed Candidate Profile
Replace `{session_id}` with the unique uuid returned from the upload command:
```bash
curl http://127.0.0.1:8000/api/v1/resume/{session_id}
```

### D. Start Mock Interview Session
Launch a mock session. Set `interview_mode` to `"Technical"`, `"HR"`, or `"Behavioral"`. Replace `{resume_session_id}`:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"resume_session_id": "{resume_session_id}", "interview_mode": "Technical", "total_questions": 5}' \
  http://127.0.0.1:8000/api/v1/interview/start
```
*Tip: Keep the returned `"interview_session_id"` to submit conversational answers.*

### E. Answer Recruiter Question (Streaming response!)
Submit answer. The `-N` flag disables curl output buffering so you can observe the Server-Sent Events (SSE) tokens streaming in real-time. Replace `{interview_session_id}`:
```bash
curl -N -X POST -H "Content-Type: application/json" \
  -d '{"session_id": "{interview_session_id}", "answer": "I scale web servers using async architectures and load balancers."}' \
  http://127.0.0.1:8000/api/v1/interview/answer
```

---

## 🐙 5. Version Control Workflow (Git)

Standard commands to push your work safely to your public GitHub repository:

### Add All Modified Files
```bash
git add .
```

### Commit Phase Changes
```bash
git commit -m "feat: complete active phase"
```

### Push to GitHub Remote Main Branch
```bash
git push origin master
```
