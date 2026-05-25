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

## 🎨 5. Next.js Frontend Operations

Before running frontend commands, make sure you have [Node.js](https://nodejs.org) installed on your system.

### Navigate to Frontend Folder
```bash
cd frontend
```

### Install Dependencies
```bash
npm install
```

### Start Development Server
Launches the Next.js dev server with fast refresh active:
```bash
npm run dev
```
Open `http://localhost:3000` in your web browser.

### Build for Production
Prepares a production-optimized build of the React application context:
```bash
npm run build
```

### Run Production Server
Serves the statically compiled pages:
```bash
npm run start
```

---

## 🐳 6. Multi-Container Orchestration (Docker Compose)

You can run both the FastAPI Python backend and the Next.js frontend simultaneously inside isolated Docker containers.

### Spin up Container Stack (Rebuild & Boot)
Automatically triggers Docker build for the backend and frontend multi-stage container and exposes them on ports `8000` and `3000` of the host system:
```bash
docker-compose up --build
```

### Run Containers in Background (Detached Mode)
```bash
docker-compose up -d --build
```

### Stop and Remove Containers
```bash
docker-compose down
```

---

## 📝 7. Monitoring Structured Loguru Logs

Logging telemetry is outputted in real-time to both standard terminal output and a rotating file stream.

### Log File Location
Log files are written locally to:
`[workspace_root]/logs/stepsai.log`

### Tail Logs in Real-time (Mac / Linux)
Watch live HTTP routing traffic, transcript analyses, and errors stream in:
```bash
tail -f logs/stepsai.log
```

---

## 🐙 8. Version Control Workflow (Git)

Standard commands to push your work safely to your public GitHub repository:

### Add All Modified Files
```bash
git add .
```

### Commit Phase Changes
```bash
git commit -m "feat: complete integrations and structured logging containerized release"
```

### Push to GitHub Remote Main Branch
```bash
git push origin master
```

