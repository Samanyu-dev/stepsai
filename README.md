# Steps AI Mock Interview Platform 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Groq](https://img.shields.io/badge/Groq%20API-f55a2a?style=for-the-badge&logo=fastapi&logoColor=white)](https://groq.com)
[![Llama-3.3](https://img.shields.io/badge/Llama%203.3%2070B-blue?style=for-the-badge)](https://meta.ai)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)

An enterprise-grade, state-of-the-art AI-powered Mock Interview system developed for the **Steps AI National-Level Online Hackathon 2026**. The platform automates resume analysis, carries out a context-aware conversational mock interview with real-time SSE streaming, deduplicates questions, conducts vague answer probing, tracks session statuses, and compiles multi-dimensional grading reports into modern, premium branded PDFs.

---

## 📌 Problem Statement

### **Problem Statement 2: AI Mock Interview Platform**
> Develop an intelligent mock interview system that:
> 1. **Analyzes Resumes**: Layout-aware text extraction for PDF and DOCX formats with programmatic skill-gap assessments.
> 2. **Adaptive Conversational AI**: A rigid multi-turn interview loop with dynamic progression, vague answer probing, and real-time Server-Sent Events (SSE) token streaming.
> 3. **Question Deduplication**: Ensures recruiter personas do not repeat previously asked topics inside a single active session.
> 4. **Rigid Performance Diagnostics**: Automated transcript grading against specific competency frameworks using low-latency Groq LLM services in JSON Mode.
> 5. **Premium PDF Export**: Automatically compiles visually appealing performance cards with circular metrics dials, radar tables, and targeted guidance recommendations.
> 
> *Domains: Conversational AI, Resume Intelligence, Automated Performance Evaluation Systems, and Career Technologies.*

---

## 📽️ Live Deployment & Demo
- 🌐 **Cosmic Frontend Client (Vercel)**: [https://stepsai-smoky.vercel.app](https://stepsai-smoky.vercel.app)
- 🧠 **FastAPI Backend Service (Render)**: [https://stepsai-backend.onrender.com](https://stepsai-backend.onrender.com)
- 🩺 **API Live Health Probe**: [https://stepsai-backend.onrender.com/health](https://stepsai-backend.onrender.com/health)

---

## 🛠️ Tech Stack

Our stack leverages a production-grade decoupled architecture. The Next.js cosmic user interface communicates directly with a multi-layered FastAPI REST framework, utilizing a persistent SQLite database and ultra-fast Groq API completions:

| Layer | Technology / Library | Role in Stack | Key Benefit |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | `Next.js 16` (React 19 App Router) | Interactive SPA Client | Dynamic SSR, layout streaming, and type safety |
| **Motion Physics** | `GSAP` (GreenSock Platform) | Micro-interactions | Pulsating audio visuals, fluid fades, and glowing card entries |
| **Styling Engine** | `Tailwind CSS 4` + CSS Variables | Glassmorphic Cosmic Design | Unified custom themes, dark-mode gradients, `#0b0f19` backdrops |
| **API Backend** | `FastAPI` (Python 3.9+) | Core Service Gateway | Extreme speed, automated OpenAPI schema, asynchronous event loops |
| **Generative AI** | `Groq Cloud API` | LLM Inference Engine | Free-tier budget, under 500ms latency, strict JSON schema output |
| **LLM Model** | `llama-3.3-70b-versatile` | Recruiter & Grader Core | 70-Billion param cognitive logic, technical/HR persona adaptivity |
| **Database** | `SQLite` (sqlite3) | Session & Data Persistence | Zero-dependency disk-based tables, structured JSON schemas |
| **Ingestion Parsing**| `PyMuPDF` + `python-docx` | File Raw Text Extractor | Ultra-fast document parsing across standard layouts |
| **Report Compiler** | `FPDF2` | Premium Branded PDF Engine | Layout grid systems, dynamic page counts, custom header banners |
| **Security Layer** | `APIKeyHeader` + `X-API-Key` | API Request Gatekeeper | Optional strict path guarding with zero client disruptions |
| **Traffic Control** | Thread-safe Sliding Window | In-memory Rate Limiter | Per-endpoint, IP-based client throttling (10/min, 60/min) |
| **Structured Logs**  | `Loguru` + Interceptors | Multi-handler Logging | Daily rotating zip folders, uvicorn stderr redirection |
| **Testing Suite** | `Pytest` + `HTTPX` TestClient | Automatic CI/CD Verification| Integrated database mocks, SSE streaming checks |
| **Deployment** | `Docker` & `Docker Compose` | Container Orchestration | Instant multi-stage compilation and service startup |

---

## 🏗️ System Architecture

Our services communicate via standard REST interfaces, using SSE streams for conversational loops, and SQLite for persistence:

```mermaid
graph TD
    Client[Next.js Premium Frontend: port 3000] -->|Upload PDF/DOCX| API_Resume[POST /api/v1/resume/upload]
    Client -->|Launch Mode Mock Session| API_Start[POST /api/v1/interview/start]
    Client -->|Answer Question SSE Stream| API_Answer[POST /api/v1/interview/answer]
    Client -->|Get Active Session Status| API_Status[GET /api/v1/interview/status/{session_id}]
    Client -->|End and evaluate session| API_End[POST /api/v1/interview/end]
    Client -->|Download PDF report| API_Report[GET /api/v1/report/{session_id}]
    Client -->|Database Health Probe| API_Health[GET /health]

    subgraph "FastAPI Backend: port 8000"
        API_Health --> DB_Check{SQLite Query Select 1}
        API_Resume --> Limit_Up[Depends: upload_limiter]
        API_Start --> Limit_Int[Depends: interview_limiter]
        API_Answer --> Limit_Int
        API_Resume --> Auth_Check[Depends: get_api_key]
        
        Parser[PyMuPDF & python-docx] --> DB[(SQLite DB: stepsai.db)]
        Engine[Interview Engine] --> DB
        Evaluator[Groq JSON Grader] --> DB
        PDF_Comp[FPDF2 Report Compiler] --> DB
        
        Parser --> LLM_Call[Groq API Client]
        Engine --> LLM_Call
        Evaluator --> LLM_Call
    end

    LLM_Call -->|Llama 3.3 70B JSON / Text| Groq_Cloud[Groq Cloud Inference Engine]
```

---

## 🚦 API Reference

The backend registers 7 primary endpoints under the `/api/v1` namespace, plus 2 base monitoring routes. Auth validation depends on `REQUIRE_AUTH` within settings:

| Endpoint | Method | Security | Parameters / Body | Description | Expected Output |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/` | `GET` | None | None | Root greeting and documentation router redirect | `{"message": "...", "docs": "/docs"}` |
| `/health` | `GET` | None | None | Active database connectivity SELECT check | `{"status": "healthy", "database": {"status": "healthy"}}` |
| `/api/v1/health` | `GET` | None | None | Lightweight service uptime diagnostic info | `{"status": "healthy", "uptime_seconds": 12.3}` |
| `/api/v1/resume/upload` | `POST` | `X-API-Key` | `file` (UploadFile), `job_role` (Query) | Layout-aware text extraction & Groq JSON profiling | `{"session_id": "uuid", "profile": {...}, "skill_gaps": [...]}` |
| `/api/v1/resume/{session_id}`| `GET` | `X-API-Key` | `session_id` (Path) | Retrieve resume profile. Enforces 24-hr session expiry | `{"session_id": "uuid", "profile": {...}, "created_at": "..."}` |
| `/api/v1/interview/start` | `POST` | `X-API-Key` | `resume_session_id`, `mode`, `difficulty` | Launches a mock session, registers syllabus schema | `{"interview_session_id": "uuid", "welcome_message": "..."}` |
| `/api/v1/interview/answer` | `POST` | `X-API-Key` | `interview_session_id`, `answer` | Submits candidate response. Streams back next question | SSE Stream chunk-by-chunk (`text/event-stream`) |
| `/api/v1/interview/status/{session_id}` | `GET` | `X-API-Key` | `session_id` (Path) | Returns active duration, index, and completion state | `{"session_id": "...", "elapsed_seconds": 142, "completed": false}` |
| `/api/v1/interview/end` | `POST` | `X-API-Key` | `interview_session_id` | Terminate session. Grades transcripts, caches FPDF | `{"session_id": "uuid", "overall_score": 85, "report": {...}}` |
| `/api/v1/report/{session_id}` | `GET` | `X-API-Key` | `session_id` (Path) | Fetches the compiled custom-branded PDF binary | PDF document stream (`application/pdf` headers) |

---

## 📁 Directory Structure Summary

```text
stepsai/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── health.py        # Service health checks and uptime loggers
│   │   │   ├── resume.py        # Size-restricted multi-format uploads & expirations
│   │   │   ├── interview.py     # SSE session start, stream answers & status checks
│   │   │   └── evaluation.py    # Session ending, Groq rubrics, PDF downloads
│   │   └── router.py            # Master endpoint namespace configuration
│   ├── core/
│   │   ├── config.py            # Unified Pydantic base settings manager
│   │   ├── db.py                # Thread-safe SQLite initialization & connection pool
│   │   ├── logging.py           # Loguru color console and rotating log routing
│   │   ├── rate_limiter.py      # Thread-safe in-memory sliding-window IP limits
│   │   ├── security.py          # Strict X-API-Key dependency validator
│   │   └── taxonomy.py          # Professional competency tables and gap analyzer
│   ├── models/
│   │   ├── resume.py            # Pydantic formats for uploaded candidate profiles
│   │   ├── interview.py         # Schema models for starting and tracking sessions
│   │   └── evaluation.py        # Model structures for scorecards & grader results
│   ├── services/
│   │   ├── resume_parser.py     # PDF & Word text extractor engines
│   │   ├── interview_engine.py  # Adaptive syllabus progression & question deduplication
│   │   ├── evaluation.py        # Premium visual FPDF2 page grid report compiler
│   │   └── llm.py               # Asynchronous Groq streams client with JSON fallback
│   ├── tests/
│   │   ├── test_resume.py       # Upload format checks and ingestion assertions
│   │   ├── test_interview.py    # Deduplication streams and status test suites
│   │   ├── test_evaluation.py   # Grader JSON assertions and PDF cache signatures
│   │   ├── test_health.py       # Base route diagnostics asserts
│   │   └── test_main.py         # Active SQLite connectivity health assertions
│   └── main.py                  # FastAPI initialization, lifespan & CORS
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── globals.css      # Dark starfield gradients and Tailwind structures
│   │       ├── layout.tsx       # Standard fonts and metadata setup
│   │       └── page.tsx         # Complex SPA glassmorphic React interactive client
│   ├── tsconfig.json            # Strict TypeScript compiler definitions
│   └── Dockerfile               # Multi-stage optimized Node deployment container
├── Dockerfile                   # Python Uvicorn production-stage build
├── docker-compose.yml           # Orchestrates Frontend, Backend & persistent volumes
├── requirements.txt             # Strict pip package configurations
├── .env.example                 # Standardized environment configuration template
├── README.md                    # System comprehensive manual (This file)
└── ARCHITECTURE.md              # Technical decision logs and data pipelines
```

---

## 🚀 Setup & Execution Guide

### Option A: Complete Docker Compose Orchestration (Recommended)
Make sure you have [Docker](https://www.docker.com/) running locally, then spin up the environment with one command:
```bash
docker-compose up --build
```
* **Cosmic Frontend Client Dashboard**: Access at `http://localhost:3000`
* **Interactive FastAPI Swagger Documents**: Access at `http://localhost:8000/docs`
* **Local Persistent Database File**: Automatically created as `stepsai.db` in your root workspace.

---

### Option B: Local Services Dev Setup

#### 1. Setup Backend API Service
1. **Initialize and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. **Install exact requirements**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. **Configure environment settings**:
   ```bash
   cp .env.example .env
   # Add your GROQ_API_KEY and set REQUIRE_AUTH=False for client testing
   ```
4. **Boot FastAPI service**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### 2. Setup Next.js Frontend Client
1. **Navigate to the frontend folder**:
   ```bash
   cd frontend
   ```
2. **Install Node packages**:
   ```bash
   npm install
   ```
3. **Run Next.js dev server**:
   ```bash
   npm run dev
   ```
4. **Open in browser**:
   Navigate to `http://localhost:3000` to interact with the platform.

---

## 🧪 Automated Testing

We maintain a rigorous test suite of 13 unit tests verifying state, parsing logic, rate limiters, session expiry timers, database schemas, and streaming delimiters.

To run the test suite, ensure your virtual environment is active, then execute:
```bash
./venv/bin/pytest -v
```

### Expected Output:
```text
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Users/apple/Desktop/stepsai/venv/bin/python3
cachedir: .pytest_cache
rootdir: /Users/apple/Desktop/stepsai
plugins: anyio-4.12.1
collecting ... collected 13 items

app/tests/test_evaluation.py::test_end_interview_session_not_found PASSED
app/tests/test_evaluation.py::test_evaluation_and_pdf_generation_flow PASSED
app/tests/test_evaluation.py::test_download_report_not_found PASSED
app/tests/test_health.py::test_health_check PASSED
app/tests/test_health.py::test_root_endpoint PASSED
app/tests/test_interview.py::test_start_interview_invalid_resume_session PASSED
app/tests/test_interview.py::test_interview_conversational_and_streaming_flow PASSED
app/tests/test_interview.py::test_interview_question_deduplication_flow PASSED
app/tests/test_interview.py::test_interview_session_status_endpoint PASSED
app/tests/test_main.py::test_database_health_probe PASSED
app/tests/test_resume.py::test_upload_resume_invalid_format PASSED
app/tests/test_resume.py::test_upload_resume_and_retrieval_flow PASSED
app/tests/test_resume.py::test_get_parsed_resume_not_found PASSED

======================== 13 passed, 5 warnings in 0.36s ========================
```

---

## 🔒 Security & Traffic Policy
* **API Access Gates**: A validated `X-API-Key` can be required on all ingest and mock session endpoints by setting `REQUIRE_AUTH=True` in `.env`.
* **Sliding-Window Throttling**: Restricts heavy uploads to max `10/min` and interactive answer submissions to max `60/min` per host IP.
* **Strict Size Enforcements**: Rejects any file payload exceeding `5MB` directly at the HTTP layer, mitigating server CPU bloat.
