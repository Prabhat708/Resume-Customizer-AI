# ResumeCraft — AI-Powered Resume Customizer

An ATS-optimized, factuality-preserving resume customizer built with Next.js, FastAPI, and Google Gemini. Tailors resumes to target job descriptions, computes deterministic evidence match scores, visualizes side-by-side bullet diffs with source provenance, and exports publication-grade A4 PDFs with zero ATS footers.

- **GitHub Repository**: [https://github.com/Prabhat708/Resume-Customizer-AI](https://github.com/Prabhat708/Resume-Customizer-AI)
- **Deployment Status**: Configured for Render (Backend) and Vercel (Frontend). Local verification completed 100%.

---

## Architecture & System Design

```text
┌────────────────────────────────┐
│      Next.js 16 Frontend       │
│  React 19 • TypeScript • CSS   │
│ (ResumePreview, Diff, Analysis)│
└───────────────┬────────────────┘
                │ HTTP / JSON / Multipart
                ▼
┌────────────────────────────────┐
│      FastAPI Python Backend    │
│  Pydantic v2 • Security Guard  │
├────────────────────────────────┤
│ 1. Document Parser (PyMuPDF)   │
│ 2. Structurer & Sanitizer      │
│ 3. Gemini LLM Customizer       │
│ 4. Factuality & Diff Auditor   │
│ 5. Heuristic Match Scorer      │
│ 6. ReportLab A4 PDF Exporter   │
└────────────────────────────────┘
```

### Technology Stack
- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Lucide icons.
- **Backend**: Python 3.11–3.13, FastAPI, Uvicorn, Pydantic v2, Google GenAI SDK (`google-genai`), PyMuPDF (`fitz`), `python-docx`, ReportLab.
- **Testing**: Pytest (102 tests), Pytest-asyncio, HTTPX, ESLint.

---

## Directory Structure

```text
resume/
├── backend/
│   ├── app/
│   │   ├── routers/          # API endpoints: health, resume, export
│   │   ├── schemas/          # Pydantic data contracts (API, analysis, resume, tailored)
│   │   ├── services/         # Core business logic: parser, structurer, Gemini, auditor, scorer, PDF exporter
│   │   ├── config.py         # Type-safe configuration from environment
│   │   ├── exceptions.py     # Domain exceptions and status code mappings
│   │   └── main.py           # FastAPI entrypoint, CORS & error handlers
│   ├── tests/                # Comprehensive test suite (102 tests)
│   ├── .env.example          # Template environment configuration
│   ├── Procfile              # Production process definition
│   ├── pyproject.toml        # Pytest & packaging configuration
│   └── requirements.txt      # Pinned production and test dependencies
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router (page.tsx, layout.tsx, globals.css)
│   │   ├── components/       # UI Components (ResumePreview, DiffView, MatchAnalysisCard, etc.)
│   │   ├── lib/              # API fetch client and typed errors
│   │   └── types/            # TypeScript interfaces matching backend schemas
│   ├── .env.example          # Frontend environment variable template
│   ├── package.json          # Frontend dependencies and scripts
│   ├── tsconfig.json         # Strict TypeScript configuration
│   └── vercel.json           # Vercel deployment configuration
├── plan/                     # Engineering design specifications
├── render.yaml               # Render Infrastructure-as-Code blueprint
├── .gitignore                # Git exclusions (secrets, venvs, artifacts)
└── README.md                 # Project documentation
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default | Required in Production |
| :--- | :--- | :--- | :---: |
| `GEMINI_API_KEY` | Google Gemini API key | `""` | **Yes** |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.5-flash` | No |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:3000` | **Yes** |
| `MAX_FILE_SIZE_MB` | Maximum allowed upload size in MB | `5` | No |
| `MAX_PAGES` | Maximum allowed pages for uploaded resumes | `10` | No |
| `MIN_EXTRACTED_CHARS` | Minimum text length for valid resume extraction | `50` | No |
| `LLM_TIMEOUT_SECONDS`| Network timeout for Gemini API calls in seconds | `45` | No |
| `MAX_RESUME_CHARS` | Maximum character length for raw resume text | `30000` | No |
| `MAX_JD_CHARS` | Maximum character length for job descriptions | `15000` | No |

### Frontend (`frontend/.env.local`)

| Variable | Description | Default | Required in Production |
| :--- | :--- | :--- | :---: |
| `NEXT_PUBLIC_API_URL` | Public base URL of the FastAPI backend | `http://localhost:8000` | **Yes** |

---

## Local Development Setup

### 1. Prerequisites
- **Python**: 3.11+ (Python 3.11, 3.12, or 3.13)
- **Node.js**: 18+ (Node 20+ recommended)
- **Git**

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from template
cp .env.example .env
# Edit .env and supply your GEMINI_API_KEY

# Start backend server
uvicorn app.main:app --reload --port 8000
```
Backend API will be live at `http://127.0.0.1:8000`. OpenAPI docs available at `http://127.0.0.1:8000/api/docs`.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local from template
cp .env.example .env.local

# Start development server
npm run dev
```
Frontend web application will be live at `http://localhost:3000`.

---

## API Documentation

### 1. Health Check
- **Endpoint**: `GET /api/v1/health`
- **Response**:
  ```json
  {
    "status": "ok",
    "version": "0.1.0",
    "model_configured": true
  }
  ```

### 2. Tailor & Analyze Resume
- **Endpoint**: `POST /api/v1/resume/customize`
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `file`: Resume document (`.pdf` or `.docx`, max 5 MB).
  - `job_description`: Target job description string (min 50 chars).
- **Response**: JSON matching `CustomizeResponse` schema (match analysis, original parsed resume, tailored resume with factuality audit warnings and bullet-level provenance).

### 3. Export ATS PDF
- **Endpoint**: `POST /api/v1/export/pdf`
- **Content-Type**: `application/json`
- **Body**: JSON payload matching `ExportPdfRequest` (`tailored_resume`).
- **Response**: Binary PDF file (`application/pdf`, attachment filename `tailored_resume.pdf`).

---

## Automated Verification Suite

Run the full automated test suite to verify functionality before submitting or deploying:

```bash
# 1. Backend Pytest Suite (102 tests)
cd backend
.\.venv\Scripts\pytest -v

# 2. Frontend ESLint
cd frontend
npm run lint

# 3. Frontend Production Build
cd frontend
npm run build
```

---

## Production Deployment Guide

### Deploy Backend to Render

1. Sign in to [Render](https://render.com/).
2. Click **New +** &rarr; **Web Service**.
3. Connect the GitHub repository: `Prabhat708/Resume-Customizer-AI`.
4. Configure service settings:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/v1/health`
5. Under **Environment Variables**, add:
   - `GEMINI_API_KEY`: *(Your Google Gemini API Key)*
   - `GEMINI_MODEL`: `gemini-2.5-flash`
   - `CORS_ORIGINS`: `https://<YOUR-FRONTEND-SUBDOMAIN>.vercel.app,http://localhost:3000`
   - `LLM_TIMEOUT_SECONDS`: `45`
   - `MAX_FILE_SIZE_MB`: `5`
6. Click **Deploy Web Service**.
7. Copy the public Render URL (e.g., `https://resumecraft-backend.onrender.com`).

### Deploy Frontend to Vercel

1. Sign in to [Vercel](https://vercel.com/).
2. Click **Add New...** &rarr; **Project** and import `Prabhat708/Resume-Customizer-AI`.
3. Configure project settings:
   - **Root Directory**: Click edit and select `frontend`.
   - **Framework Preset**: `Next.js`.
4. Under **Environment Variables**, add:
   - `NEXT_PUBLIC_API_URL`: `https://<YOUR-BACKEND-SUBDOMAIN>.onrender.com`
5. Click **Deploy**.
6. Once deployed, copy your production Vercel URL and add it to the backend `CORS_ORIGINS` on Render.

---

## Known Limitations & Security Considerations

1. **Cold Start Latency**: On free-tier cloud platforms (e.g. Render free tier), the backend container sleeps after inactivity; initial requests may take 30–50 seconds to spin up.
2. **Deterministic Match Scoring**: The match score is a deterministic heuristic based on extracted textual evidence from the uploaded resume. It is not an official Applicant Tracking System score.
3. **Factuality Enforcement**: ResumeCraft strictly rejects hallucinating metrics, skills, or employment history. If a candidate does not have formal employment in a specific technology, it is classified under project/skills evidence or noted as an informational item.
4. **Privacy Protection**: Uploaded files and extracted resume texts are processed in memory and never logged, stored in persistent databases, or leaked to browser bundles.
