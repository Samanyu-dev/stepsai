# Steps AI Mock Interview Platform - Architecture & Decision Record (ADR)

This document details the system design, key architectural decision records (ADR), and detailed data pipelines governing the **Steps AI Mock Interview Platform**.

---

## 🛠️ Architectural Decision Records (ADR)

### **ADR 01: Persistent SQLite Database over PostgreSQL / MongoDB**
* **Context**: The mock interview system requires state persistence (resumes, conversation history, metrics, and compiled PDF reports) that survives application restarts. In hackathon conditions, setup complexity must be minimal, yet robust enough for production-like demonstration.
* **Decision**: Adopt **SQLite** (`sqlite3`) as the core database layer, configuring it in a persistent localized file (`stepsai.db`).
* **Rationale**:
  1. **Zero Setup Cost**: SQLite is embedded directly within Python, requiring no external docker database service setup, credentials management, or localized post-installation scripts.
  2. **Storage and Volume Management**: Session data is fully persisted on the filesystem and can be mapped cleanly via Docker Volumes to ensure durability.
  3. **Performance**: For a single-user or small-scale testing team, SQLite provides sub-millisecond read/write speeds, handling structured JSON string columns (`messages_json`, `profile_json`) and raw PDF BLOB files (`pdf_bytes`) with ease.
  4. **Robust Schema Migration**: Implemented programmatic safety triggers during server lifespan startup (`init_db()`) to automatically execute schemas and structural column updates (e.g., `ALTER TABLE resumes ADD COLUMN created_at`).

---

### **ADR 02: Server-Sent Events (SSE) over Bidirectional WebSockets**
* **Context**: When a candidate answers a mock interview question, the Groq LLM should stream the recruiter's subsequent response token-by-token back to the Next.js UI to construct a high-fidelity visual interaction.
* **Decision**: Implement **Server-Sent Events (SSE)** using FastAPI's standard `StreamingResponse` set to `text/event-stream` headers, instead of bidirectional WebSockets.
* **Rationale**:
  1. **Simplicity and Reliability**: SSE operates over standard HTTP/1.1 or HTTP/2, requiring no extra websocket handshakes, protocols, or custom network configuration in reverse proxies.
  2. **Unidirectional Suitability**: The conversational streaming is strictly unidirectional (the client submits a full answer payload once, and the backend streams back the recruiter's response in chunks). SSE is perfectly matched for this pattern.
  3. **Seamless Security Integration**: Since SSE is standard HTTP, it respects our FastAPI security dependency chains (`Depends(get_api_key)`) and IP rate-limiting middleware seamlessly out of the box, whereas WebSockets require custom connection-handshake authentication overrides.
  4. **Automatic Reconnection**: Browsers natively manage SSE reconnections, reducing frontend state machine complexity.

---

### **ADR 03: Thread-Safe In-Memory Sliding Window Rate Limiting over Redis**
* **Context**: To prevent denial-of-service attempts or runaway API billing on Groq, backend upload and response endpoints must be protected from high-frequency requests.
* **Decision**: Implement a **thread-safe, in-memory sliding-window rate limiter** utilizing a thread Lock and memory timestamps list, bypassing external Redis dependencies.
* **Rationale**:
  1. **Lightweight Profile**: Adding an external Redis cache container increases container memory foot-print and complicates single-instance orchestration. An in-memory dict handles this with zero overhead.
  2. **Mathematical Accuracy**: A sliding window removes the "burst reset" vulnerability found in simple fixed-window limiters. It calculates the exact elapsed request volume over the preceding 60 seconds.
  3. **Thread Safety**: Wrapped in a Python `threading.Lock()` block, preventing concurrent memory race conditions from multiple incoming Uvicorn worker threads.

---

### **ADR 04: Groq Llama-3.3-70B over Llama-3-8B**
* **Context**: Parsing layout-heavy resumes into strict profiles, conducting deep technical interviews, and grading dialogues against complex rubrics requires robust reasoning capabilities.
* **Decision**: Deploy Groq's **`llama-3.3-70b-versatile`** model for all conversational streaming, JSON profiling, and metric evaluations.
* **Rationale**:
  1. **Cognitive Reasoning**: The 70B parameter variant has vastly superior capabilities in taxonomy mapping, semantic grading, and understanding complex programming concepts compared to the smaller 8B model.
  2. **Groq's Free-Tier Latency**: Groq's LPUs stream Llama 3.3 tokens at over 200 tokens/sec. Text generation takes under 500ms to begin, providing a premium experience that matches paid models.
  3. **Rigid JSON Compliance**: Used in combination with Groq's JSON Mode (`response_format={"type": "json_object"}`), the 70B model reliably adheres to complex Pydantic JSON schemas, avoiding parsing exceptions during resume ingestion and grading.

---

## 📈 Enterprise Data Pipelines

### **1. Resume Ingestion & Intelligence Pipeline**
```
Candidate Document (PDF / DOCX) 
   │
   ▼
[REST controller: POST /api/v1/resume/upload]
   │
   ├── Checks size threshold (<5MB) and validates file format
   ├── Throttles client IP via sliding window upload limiter (max 10/min)
   └── Validates headers using optional X-API-Key gate
   │
   ▼
[PyMuPDF / python-docx Parsing Engine] 
   │
   ▼
Extracted Raw Text Block
   │
   ▼
[Groq Service: Llama-3.3-70B JSON Mode]
   │
   ├── Extracted JSON Profile (Name, Contact, Experience Years, Core Skills)
   └── Programmatic skill gap calculations (against app/core/taxonomy.py mappings)
   │
   ▼
[SQLite DB Persistence]
   │
   └── Writes record into 'resumes' table (session_id, profile_json, resume_text, created_at)
   │
   ▼
Returns UUID Session Token and parsed profile JSON back to the Next.js Client
```

---

### **2. State-Aware Conversational Interview Loop**
```
Candidate chooses Mode (Technical, HR, Behavioral) & Difficulty (Easy, Medium, Hard)
   │
   ▼
[REST controller: POST /api/v1/interview/start]
   │
   ├── Fetches corresponding resume profile from SQLite DB
   ├── Initializes Recruiter Alex syllabus and default prompts
   └── Persists new active session inside 'interviews' table
   │
   ▼
Next.js UI mounts the Conversational Room & Candidate answers a question
   │
   ▼
[REST controller: POST /api/v1/interview/answer]
   │
   ├── Throttles IP via sliding window interview limiter (max 60/min)
   ├── Fetches previous dialogue history and asked questions from SQLite DB
   ├── Runs Vague Answer Heuristics (response length, filler words markers)
   │     ├── Triggered: Prepend targeted probe guidance instruction to LLM prompt
   │     └── Not Triggered: Standard progression flow
   ├── Injects asked_questions list to avoid Groq duplicate topics
   │
   ▼
[Groq Streaming completions API]
   │
   └── Streams response back to FastAPI, which forwards it to Client as SSE chunks
   │
   ▼
[Post-Stream Background Logger]
   └── Updates SQLite 'interviews' table with new dialogue records & active question index
```

---

### **3. Performance Evaluation & Branded PDF Compilation Pipeline**
```
Candidate clicks "End and Evaluate" button in Next.js Client
   │
   ▼
[REST controller: POST /api/v1/interview/end]
   │
   ├── Fetches active interview message transcript and parsed resume from SQLite
   ├── Bundles transcript turns into detailed grading prompt
   │
   ▼
[Groq Grader Service: JSON Mode]
   │
   ├── Evaluates overall score (1-100%) and target average benchmarking
   └── Computes specific metric values (Technical Accuracy, Communication, etc.)
   │
   ▼
[FPDF2 PDF Report Compiler]
   │
   ├── Instantiates custom FPDF performance page builder
   ├── Binds corporate headers, side margins, and footer pagination enums
   ├── Renders overall scores card with custom brand banners
   ├── Compiles strengths/weaknesses layout alongside specific missing skill recommendations
   └── Outputs final compiled PDF report file bytes
   │
   ▼
[SQLite DB Persistence]
   │
   └── Caches overall_score, report_json, and pdf_bytes in 'evaluations' table
   │
   ▼
Next.js client fetches GET /api/v1/report/{session_id} to instantly download compiled PDF
```
