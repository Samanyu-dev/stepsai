# Steps AI Mock Interview Platform 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Groq](https://img.shields.io/badge/Groq%20API-f55a2a?style=for-the-badge&logo=fastapi&logoColor=white)](https://groq.com)
[![Llama-3.3](https://img.shields.io/badge/Llama%203.3%2070B-blue?style=for-the-badge)](https://meta.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

An advanced, enterprise-grade AI-powered Mock Interview system developed for the **Steps AI National-Level Online Hackathon 2026**. The platform automates candidate assessments by analyzing resumes, carrying out a context-aware conversational mock interview with real-time SSE streaming, and providing automated multi-dimensional grading reports.

---

## 📌 Selected Problem Statement

### **Problem Statement 2: AI Mock Interview Platform**
> Develop an intelligent mock interview system that:
> 1. Analyzes uploaded resumes (PDF & DOCX).
> 2. Conducts personalized, conversational interviews with streaming answers.
> 3. Generates role-based questions (HR, Technical, Behavioral).
> 4. Evaluates candidate responses.
> 5. Provides comprehensive feedback and improvement suggestions.
> 
> *Domains Involved: Conversational AI, Resume Intelligence, AI Evaluation Systems, Career Technology.*

---

## 📽️ Demo Video
> 🎬 **Demo Video Link**: [Insert YouTube or Google Drive Link Here]

---

## 🛠️ Tech Stack Used

### 🧠 Backend (FastAPI Python Service)
- **Core Framework**: [FastAPI](https://fastapi.tiangolo.com/) (High-performance Python Web Framework)
- **Generative AI & LLM Engine**: [Groq llama-3.3-70b-versatile](https://console.groq.com/) (Free Tier, ultra-low latency)
- **PDF Extraction**: [PyMuPDF / fitz](https://pymupdf.readthedocs.io/) (Ultra-fast PDF text parsing)
- **DOCX Extraction**: [python-docx](https://python-docx.readthedocs.io/) (Structured Word Document parsing)
- **Data Validation & Settings**: [Pydantic V2 & Pydantic-Settings](https://docs.pydantic.dev/)
- **Testing Suite**: [Pytest](https://docs.pytest.org/) & [HTTPX](https://www.python-httpx.org/) (Async testing)
- **Structured Telemetry Logging**: [Loguru](https://github.com/Delgan/loguru) (Async-safe, colorized rotating and compressed logs)
- **Process Manager / Server**: [Uvicorn](https://www.uvicorn.org/)

### 🎨 Frontend (Next.js Premium Client)
- **Core Framework**: [Next.js 16 (React 19 App Router)](https://nextjs.org/) (Production-grade SSR & SPA)
- **Layout & Styling**: [Tailwind CSS 4](https://tailwindcss.com/) (Next-generation utility CSS engine)
- **High-Performance Animations**: [GSAP (GreenSock Animation Platform)](https://greensock.com/gsap/) (Stunning, hardware-accelerated transitions & motion design)
- **Interactive UI Icons**: [Lucide React](https://lucide.dev/) (Sleek pixel-perfect SVG vectors)

---

## 🏗️ System Architecture & Design

The platform is designed around a decoupled, service-oriented architecture. The Next.js frontend communicates directly with the FastAPI REST controllers, rendering dynamic SSE streams and fetching compiled report PDFs seamlessly.

```mermaid
graph TD
    Client[Next.js Premium Frontend: port 3000] -->|Upload PDF/DOCX| API_Resume[POST /api/v1/resume/upload]
    Client -->|Launch Mode Mock Session| API_Start[POST /api/v1/interview/start]
    Client -->|Answer Question SSE Stream| API_Answer[POST /api/v1/interview/answer]
    Client -->|End and evaluate session| API_End[POST /api/v1/interview/end]
    Client -->|Download PDF report| API_Report[GET /api/v1/report/{session_id}]

    subgraph "FastAPI Backend: port 8000"
        API_Resume --> Parser[PyMuPDF & python-docx]
        API_Start --> Engine[Interview Engine]
        API_Answer --> Engine
        API_End --> Evaluator[Groq JSON Grader]
        API_Report --> Evaluator
        
        Parser --> ResumeStore[InMemory Resume Cache]
        Engine --> InterviewStore[InMemory Dialogue Cache]
        
        Parser --> LLM[Groq Llama 3.3 70B Service]
        Engine --> LLM
        Evaluator --> LLM
    end
```

---

## ⚙️ Implementation Approach & Workflow

The platform delivers a 100% complete, context-aware interview preparation loop:

1. **Resume Intelligence (Phase 2)**: Candidate uploads their resume. `PyMuPDF` or `python-docx` extracts raw text. A Groq JSON schema parser profiles details (skills, roles, experience years, strengths) and caches them in memory.
2. **recruiter Alex Syllabus (Phase 3)**: Candidate enters the room after choosing mode (`HR`, `Technical`, `Behavioral`) and difficulty. Recruiter Alex automatically detects experience levels and welcomes them with the first custom question.
3. **SSE Conversational Room (Phase 3 & 5)**: Answers are submitted. Telemetry streams tokens letter-by-letter back to the Next.js screen via Server-Sent Events (`text/event-stream`). GSAP renders characters in fluid fades.
4. **Performance Diagnostics & PDF Report (Phase 4)**: Groq grades each conversation turn on a 1-10 scale (Communication Clarity, Technical Depth, Relevance, Confidence). `fpdf2` compiles this into a custom-branded assessment PDF ready for download.
5. **Loguru Interceptors & Docker Compose (Phase 5)**: Standard logging outputs colored live traces and writes weekly rotating logs under `/logs`. The multi-container setup launches the entire stack in one command.

---

## 🌟 Features & Functionalities

- [x] **Full REST API scaffolding** with automated OpenAPI docs (/docs)
- [x] **Modular enterprise layout** decoupling configurations, routing, models, and services
- [x] **Resume Intelligence**: Multi-format PDF and Word DOCX parsing and structured Groq JSON profiling (Phase 2)
- [x] **Resume Session Stores**: Cache parsed candidate details in-memory, retrievable via GET `/resume/{session_id}` (Phase 2)
- [x] **Conversational Recruiter SSE Stream**: Multi-turn dialogue with real-time SSE streaming, supporting HR, Technical, and Behavioral modes across Junior, Mid, and Senior difficulty levels (Phase 3)
- [x] **Rubric Grading & PDF Export**: Detailed performance sheets with visual scores (Phase 4)
- [x] **Next.js Premium SPA**: Responsive Dark Cosmic design with glassmorphism, glowing custom scorecards, pulsating audio visualizers, and GSAP reveals (Phase 5)
- [x] **Rotating Loguru Logs**: Active interceptor rerouting standard python and uvicorn traces into rotating logs under `logs/stepsai.log` (Phase 5)
- [x] **Docker containerization**: Discrete Dockerfiles for both services and parent orchestrating `docker-compose.yml` (Phase 5)

---

## 🔑 Environment Variables Required

Create a `.env` file in the root directory based on `.env.example`:

| Variable Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `PROJECT_NAME` | String | Title of the API project | `Steps AI Mock Interview Platform` |
| `ENV` | String | Running stage (`development` or `production`) | `development` |
| `HOST` | String | Network address to bind the server | `0.0.0.0` |
| `PORT` | Integer | System port to open for the server | `8000` |
| `LOG_LEVEL` | String | Verbosity of terminal output (`info`, `debug`, etc.) | `info` |
| `GROQ_API_KEY` | String | API credential key from Groq Console | *Required for all LLM operations* |

---

## 🚀 Setup Instructions to Run Locally

### Option A: Running via Docker Compose (Recommended)
Make sure you have [Docker](https://www.docker.com/) running on your system, then build and boot both tiers:
```bash
docker-compose up --build
```
- Open `http://localhost:3000` to interact with the premium Next.js dashboard.
- Open `http://localhost:8000/docs` to access the interactive FastAPI Swagger specs.

---

### Option B: Running Local Services Individually

#### 1. Setup Backend API
1. **Initialize virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
2. **Install requirements**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Insert your Groq API Key inside .env
   ```
4. **Boot FastAPI application**:
   ```bash
   uvicorn app.main:app --reload
   ```

#### 2. Setup Next.js Frontend
1. **Navigate to folder**:
   ```bash
   cd frontend
   ```
2. **Install node modules**:
   ```bash
   npm install
   ```
3. **Run Next.js dev server**:
   ```bash
   npm run dev
   ```
4. **Open in browser**:
   Navigate to `http://localhost:3000`.

---

## 🧪 Running Automated Tests

Make sure your virtual environment is active, then execute:
```bash
pytest -v
```
All 10 test cases covering resume parsing, SSE streaming, turn-based dialogue, and PDF generation will run and pass cleanly.

