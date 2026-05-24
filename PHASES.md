# 📅 Steps AI Hackathon 2026 - Phase-wise Roadmap

This file tracks the status, goals, and technological stacks utilized across each implementation phase of the **AI Mock Interview Platform**.

---

## 🗺️ Phase Summary

| Phase | Description | Status | Target Date / Time |
| :--- | :--- | :---: | :---: |
| [Phase 1](#phase-1--scaffold-everything-current-phase) | Project Scaffolding & FastAPI Skeleton | **IN PROGRESS** | Day 1 |
| [Phase 2](#phase-2--resume-intelligence) | Resume Intelligence & Structured Extraction | *PENDING* | Day 2 |
| [Phase 3](#phase-3--the-interview-engine) | Conversational Mock Interview Engine | *PENDING* | Day 3-4 |
| [Phase 4](#phase-4--evaluation-and-feedback) | Scoring, Rubrics & PDF Report Generator | *PENDING* | Day 5 |
| [Phase 5](#phase-5--integration-and-polish) | Error Handling, Logging & Containerization | *PENDING* | Day 6 |
| [Phase 6](#phase-6--submission) | Final Demos, Documentation & Tags | *PENDING* | Day 7 |

---

## 🔍 Phase Details

### Phase 1 — Scaffold Everything (Current Phase)
* **Status**: 🛠️ **In Progress / Scaffolding complete, running checks**
* **Goals**:
  - Establish a clean, professional, enterprise-grade directory structure for a Python backend.
  - Setup core settings management using `pydantic-settings` to handle environmental inputs.
  - Implement a basic REST controller `/health` to verify system health, runtime parameters, and config bindings.
  - Deliver initial files required for Day 1 evaluator visibility (`.env.example`, `requirements.txt`, `.gitignore`, `README.md`, `PHASES.md`).
* **Tech Stack**: Python 3.10+, FastAPI, Pydantic Settings, Pytest.
* **Services / Libraries**: Uvicorn.

---

### Phase 2 — Resume Intelligence
* **Status**: ⏳ *Pending (Awaiting Phase 1 Approval)*
* **Goals**:
  - Enable PDF uploads through FastAPI `UploadFile` endpoint.
  - Implement extremely high-performance text extraction from resumes using `PyMuPDF` (fitz).
  - Feed extracted raw content to Claude 3.5 Sonnet using fine-tuned prompt structures requesting response outputs matching a strict JSON schema.
  - Parse resume intelligence into Pydantic models containing: estimated job role, skill matching lists, estimated experience tier, and key career bullet summaries.
* **Tech Stack**: FastAPI, PyMuPDF (fitz), Pydantic validation, Anthropic Claude 3.5.
* **Services / Libraries**: official `anthropic` SDK.

---

### Phase 3 — The Interview Engine
* **Status**: ⏳ *Pending*
* **Goals**:
  - Build a multi-turn conversation manager enabling candidates to answer questions and receive relevant follow-ups.
  - Develop system prompts modeling Claude as an empathetic, professional tech recruiter.
  - Incorporate context from Phase 2 (parsed resume) to target behavioral, technical, and role-specific concepts.
  - Implement in-memory conversation state persistence supporting clean session ID bindings.
* **Tech Stack**: FastAPI, Anthropic Claude 3.5.
* **Services / Libraries**: official `anthropic` SDK.

---

### Phase 4 — Evaluation and Feedback
* **Status**: ⏳ *Pending*
* **Goals**:
  - Program real-time evaluation services that analyze candidate answers against standard evaluation parameters (relevance, clarity, technical accuracy).
  - Aggregate scores dynamically to build an overall percentage score out of 100.
  - Synthesize custom improvement suggestions and target technical skill gaps.
  - Export beautiful, comprehensive candidate feedback summaries (available as clean raw JSON structures or compile-ready PDF reports).
* **Tech Stack**: FastAPI, Anthropic Claude, ReportLab (for PDF generation).
* **Services / Libraries**: Claude 3.5 API.

---

### Phase 5 — Integration and Polish
* **Status**: ⏳ *Pending*
* **Goals**:
  - Implement global error logging and exception handlers preventing raw stack traces from reaching callers.
  - Introduce file-system rotation logs using standard Python `logging`.
  - Write detailed tests targeting PDF upload and conversational state flows.
  - Optimize prompt caching elements to minimize token latency.
  - Create a lightweight `Dockerfile` to guarantee uniform runtimes.
* **Tech Stack**: Docker, Python standard `logging`, Pytest.
* **Services / Libraries**: Uvicorn, Docker Engine.

---

### Phase 6 — Submission
* **Status**: ⏳ *Pending*
* **Goals**:
  - Produce a descriptive walkthrough demonstrating endpoints and core system capabilities.
  - Polish the `README.md` to display all relevant schema diagrams.
  - Create final GitHub release tags for steps-based progression.
* **Tech Stack**: Documentation, Video recording.
* **Services / Libraries**: GitHub.
