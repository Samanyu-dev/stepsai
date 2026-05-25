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

- **Core Framework**: [FastAPI](https://fastapi.tiangolo.com/) (High-performance Python Web Framework)
- **Generative AI & LLM Engine**: [Groq llama-3.3-70b-versatile](https://console.groq.com/) (Free Tier, ultra-low latency)
- **PDF Extraction**: [PyMuPDF / fitz](https://pymupdf.readthedocs.io/) (Ultra-fast PDF text parsing)
- **DOCX Extraction**: [python-docx](https://python-docx.readthedocs.io/) (Structured Word Document parsing)
- **Data Validation & Settings**: [Pydantic V2 & Pydantic-Settings](https://docs.pydantic.dev/)
- **Testing Suite**: [Pytest](https://docs.pytest.org/) & [HTTPX](https://www.python-httpx.org/) (Async testing)
- **Process Manager / Server**: [Uvicorn](https://www.uvicorn.org/)

---

## 🏗️ Backend Architecture & System Design

The system is built on clean, modular, and testable design principles, decoupling network request layers, business workflows, and external service providers:

```mermaid
graph TD
    Client[HTTP Client / API Consumer] -->|REST API Request| FastAPI[FastAPI App / main.py]
    FastAPI -->|Routing| Routers[API Routers: app/api]
    
    subgraph "Core Business Services"
        Routers -->|Parse PDF/DOCX| Parser[Resume Parser Service]
        Routers -->|Manage Conversation| Engine[Interview Engine Service]
        Routers -->|Analyze Responses| Evaluator[Evaluation Service]
    end
    
    subgraph "Integrations & State"
        Parser -->|Raw Context| LLMService[LLM Service Interface]
        Engine -->|Prompt Template / SSE Chat| LLMService
        Evaluator -->|Rubric Analysis| LLMService
        
        LLMService -->|API Call| Groq[Groq Llama 3.3 70B / LLM]
        
        Parser -->|Cache Profile| ResumeStore[In-Memory Resume Store]
        Engine -->|Save/Restore Session| Store[In-Memory Interview Store]
    end
    
    FastAPI -->|Config Injection| Settings[Pydantic Settings]
```

---

## ⚙️ Implementation Approach & Workflow

The pipeline consists of four key phases:

1. **Resume Ingestion & Caching**: The candidate uploads their resume (PDF or DOCX). `PyMuPDF` or `python-docx` extracts the raw text. It is passed to Groq llama-3.3 using JSON Mode, returning a clean, validated JSON schema containing skills, experiences, and estimated job roles. This profile is stored in an in-memory session cache mapped to a unique `session_id`.
2. **Personalized Session Launch**: The candidate starts the mock interview via `/interview/start` selecting a mode (`HR`, `Technical`, `Behavioral`) and difficulty level. The engine retrieves their parsed resume from the session cache and returns the first question (Q1).
3. **SSE Streaming Conversation**: Candidate responses are submitted to `/interview/answer`. The engine retrieves history, invokes Groq, and yields recruiter follow-ups and next questions in real-time using Server-Sent Events (`text/event-stream`).
4. **Multi-Dimensional Grading**: Individual answers are graded (1-10) for clarity, technical depth, and relevance. A compiled PDF report outlines gaps and growth areas.

---

## 🌟 Features & Functionalities

- [x] **Full REST API scaffolding** with automated OpenAPI docs (/docs)
- [x] **Modular enterprise layout** decoupling configurations, routing, models, and services
- [x] **Resume Intelligence**: Multi-format PDF and Word DOCX parsing and structured Groq JSON profiling (Phase 2)
- [x] **Resume Session Stores**: Cache parsed candidate details in-memory, retrievable via GET `/resume/{session_id}` (Phase 2)
- [x] **Conversational Recruiter SSE Stream**: Multi-turn dialogue with real-time SSE streaming, supporting HR, Technical, and Behavioral modes across Junior, Mid, and Senior difficulty levels (Phase 3)
- [x] **Rubric Grading & PDF Export**: Detailed performance sheets with visual scores (Phase 4)
- [ ] **Docker containerization & structured logs** (Phase 5)

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

### 1. Prerequisites
- Python 3.11 or higher
- Git

### 2. Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/YOUR_GITHUB_USERNAME/stepsai.git
   cd stepsai
   ```

2. **Create a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Open .env and insert your GROQ_API_KEY
   ```

5. **Start the Application**:
   ```bash
   uvicorn app.main:app --reload
   ```
   
   The server will start running at `http://127.0.0.1:8000`.

6. **Interactive Documentation**:
   - Access Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Access Redoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Running Automated Tests

We use `pytest` for automated test suites:

```bash
pytest
```
