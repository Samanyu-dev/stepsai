# Steps AI Mock Interview Platform - Deployment & Verification Guide

This guide details the step-by-step instructions to deploy, configure, and verify the Steps AI Mock Interview Platform on production environments (**Render** for the FastAPI backend, and **Vercel** for the Next.js frontend).

---

## 🧠 Backend Deployment (Render)

We leverage Render's native **Blueprints** infrastructure which reads `render.yaml` to spin up both a high-performance **PostgreSQL database** and a **FastAPI Python web service** in unison.

### **Step-by-Step Instructions:**
1. **Prepare and Push Code**: Ensure all changes are committed and pushed to your GitHub repository.
2. **Go to Render Console**: Navigate to [render.com](https://render.com/) and sign in.
3. **Launch Blueprint**:
   - Click **New** (top-right) and select **Blueprint**.
   - Connect your GitHub repository containing the project.
4. **Deploy Service**:
   - Render automatically parses `render.yaml` and displays the configured components (`stepsai-backend` web service and `stepsai-db` PostgreSQL instance).
   - In the **Specified configurations** fields, input the following environment variables:
     - `GROQ_API_KEY`: Paste your API credential key obtained from [console.groq.com](https://console.groq.com/).
     - `API_KEY`: Input `stepsai_hackathon_2026_key` (used to secure endpoints via headers).
     - `CORS_ORIGINS`: Set as `http://localhost:3000,https://stepsai-smoky.vercel.app` (binds local dev and your Vercel frontend URL).
   - Click **Apply** / **Deploy**.
5. **Get Your Backend live URL**:
   - Once compilation and database initialization finishes, copy your generated web service URL from the dashboard.
   - **Target Live URL Format**: `https://stepsai-backend.onrender.com`

---

## 🌐 Frontend Deployment (Vercel)

The Next.js premium космический dashboard is optimized for Vercel's edge network, building in seconds using our pre-packaged `vercel.json` instructions.

### **Step-by-Step Instructions:**
1. **Go to Vercel Console**: Sign in at [vercel.com](https://vercel.com/).
2. **Import Repo**: Click **Add New** -> **Project** and import your GitHub repository.
3. **Configure Project Settings**:
   - **Root Directory**: **MUST** set this to `frontend/` (since our frontend code lives in a monorepo subfolder).
   - **Framework Preset**: Auto-detects as **Next.js**.
   - **Build Command**: `npm run build` (falls back to `vercel.json`).
4. **Define Environment Variable**:
   - Under **Environment Variables**, add the following key-value pair:
     - **Key**: `NEXT_PUBLIC_API_URL`
     - **Value**: `https://stepsai-backend.onrender.com` (paste your copied Render live URL here).
5. **Deploy**: Click **Deploy**. Vercel will build, optimize static chunks, and route it to edge servers in seconds.
   - **Target Live URL Format**: `https://stepsai-smoky.vercel.app`

---

## 🚦 Post-Deployment Alignments (CORS & Security Keys)
1. **CORS Update on Render**:
   - Now that your Vercel frontend URL is live, go to your Render Web Service dashboard -> **Environment** page.
   - Ensure `CORS_ORIGINS` includes your official Vercel domain:
     `CORS_ORIGINS=http://localhost:3000,https://stepsai-smoky.vercel.app`
   - Save changes. Render applies the CORS rules instantly.
2. **Security Gates Validation**:
   - `REQUIRE_AUTH` is pre-configured to `true` on the Render web service environment to lock down endpoints.
   - All REST requests must pass the `X-API-Key: stepsai_hackathon_2026_key` header credential.

---

## 🧪 Post-Deployment Endpoint Verification (`curl` command examples)

You can verify that your production services are active, connected, and fully secure by executing these standard `curl` commands directly from your local terminal.

### **1. Complete Database Health Connection Probe**
Assert that the backend connects successfully to the persistent PostgreSQL instance:
```bash
curl -X GET https://stepsai-backend.onrender.com/health
```
**Expected Response (HTTP 200 OK):**
```json
{
  "status": "healthy",
  "app_name": "Steps AI Mock Interview Platform",
  "database": {
    "status": "healthy",
    "error": null
  }
}
```

---

### **2. Lightweight Uptime check**
Assert that the FastAPI event loops are active and track system uptime:
```bash
curl -X GET https://stepsai-backend.onrender.com/api/v1/health
```
**Expected Response (HTTP 200 OK):**
```json
{
  "status": "healthy",
  "app_name": "Steps AI Mock Interview Platform",
  "environment": "production",
  "uptime_seconds": 1824.5
}
```

---

### **3. Ingestion & Resume Intelligence Upload (Locking Auth)**
Simulate a PDF resume upload. This command attaches the required `X-API-Key` auth headers and uploads a file chunk:
```bash
# Note: Replace "/path/to/resume.pdf" with any valid PDF or DOCX file path on your local computer
curl -X POST https://stepsai-backend.onrender.com/api/v1/resume/upload \
  -H "X-API-Key: stepsai_hackathon_2026_key" \
  -F "file=@/path/to/resume.pdf"
```
**Expected Response (HTTP 200 OK):**
```json
{
  "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3d4bad",
  "profile": {
    "name": "Jane Doe",
    "job_role": "Backend Engineer",
    "experience_years": 4,
    "seniority": "Mid",
    "skills": ["Python", "FastAPI", "SQL", "Docker"],
    "summary": "Experienced engineer specializing in distributed REST interfaces and database migrations.",
    "skill_gap_analysis": ["Git", "Algorithms", "Testing"]
  }
}
```

---

### **4. Mock Interview Session Launch**
Launch a state-aware mock session using the parsed resume token:
```bash
# Note: Replace "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3d4bad" with the session_id obtained from the previous upload response
curl -X POST https://stepsai-backend.onrender.com/api/v1/interview/start \
  -H "X-API-Key: stepsai_hackathon_2026_key" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3d4bad",
    "interview_mode": "Technical",
    "total_questions": 5
  }'
```
**Expected Response (HTTP 200 OK):**
```json
{
  "interview_session_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "resume_session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3d4bad",
  "first_question": "Hello Jane! Welcome to our technical interview. I see you have 4 years of experience as a Backend Engineer with expertise in Python and FastAPI. To kick things off, could you explain the differences between relational database indexing and simple document lookup in your past database migrations?",
  "interview_mode": "Technical",
  "difficulty_level": "Mid",
  "total_questions": 5
}
```
