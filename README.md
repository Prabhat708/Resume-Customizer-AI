# ResumeCraft — AI Resume Customizer

**Live Demo:** [https://resume.erprabhat.in](https://resume.erprabhat.in/)

An ATS-aligned, factuality-preserving resume customizer built with Next.js, FastAPI, and Google Gemini. Tailors resumes to target job descriptions, computes deterministic evidence-based match scores, visualizes side-by-side bullet diffs with source provenance, and exports ATS-readable A4 PDFs.

---

## Live Application

* **Frontend:** [https://resume.erprabhat.in](https://resume.erprabhat.in/)
* **Backend Health:** [https://resumecraft-api-xhor.onrender.com/api/v1/health](https://resumecraft-api-xhor.onrender.com/api/v1/health)
* **GitHub Repository:** [https://github.com/Prabhat708/Resume-Customizer-AI](https://github.com/Prabhat708/Resume-Customizer-AI)

> **Note:** The backend runs on Render's free tier, so the first request after inactivity may take longer while the service wakes up.

---

## Architecture Overview

* **Frontend (`/frontend`):** Next.js 16 App Router, React 19, TypeScript, Tailwind CSS, and Lucide icons.
* **Backend (`/backend`):** FastAPI, Pydantic v2, Google Gemini API, PyMuPDF (`fitz`), `python-docx`, and ReportLab.
* **Factuality & Provenance Engine:** Checks customized content against source resume evidence and helps prevent fabricated metrics, unsupported skills, and unsubstantiated employment claims.
* **Scoring Engine:** Computes evidence-based match scores using a deterministic weighted formula.
* **PDF Export:** Generates ATS-readable A4 resume PDFs.

---

## Prerequisites

* **Python 3.11+**
* **Node.js 20+** recommended, with `npm`
* **Google Gemini API Key** for live AI customization

---

## Quickstart Setup

### 1. Backend Setup

```bash
cd backend

# Create a virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment configuration
cp .env.example .env
```

Edit `backend/.env` and configure your Gemini API key:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.8-flash
```

> **Security Note:** Keep your API key private. Never commit `.env` or expose API keys in frontend environment variables.

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`.

* **Health endpoint:** `http://127.0.0.1:8000/api/v1/health`

---

### 2. Frontend Setup

Open a separate terminal:

```bash
cd frontend

# Install dependencies
npm install

# Create local environment configuration
cp .env.example .env.local
```

Configure `frontend/.env.local` to point to your local backend:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Start the frontend:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000/).

---

## Running Verification & Tests

### Backend Automated Test Suite

Run the backend tests from the `backend` directory:

```bash
python -m pytest -v
```

The latest project verification report recorded **102 passing backend tests**. Run the suite locally to verify your current checkout.

**Coverage includes:**
* PDF/DOCX parsing and validation
* Corrupt and encrypted document handling
* Factuality auditing and provenance tracking
* Match-score calculations
* PDF export and layout validation
* Special characters and long URLs

### Frontend Lint and Production Build

From the `frontend` directory:

```bash
npm run lint
npm run build
```

---

## Core Capabilities & Engineering Highlights

### 1. Factuality and Provenance
* Customized content is checked against information in the source resume.
* Customized bullets retain links to source evidence through `source_bullet_id`.
* Unsupported metrics and claims can trigger auditor warnings or validation failures.
* Employment experience and personal project evidence are distinguished.

### 2. Deterministic Match Scoring
* Uses a backend mathematical formula rather than asking the language model to invent a score.
* **Requirement weights:** Required = 1.5×; Preferred = 1.0×.
* **Evidence values:** Full = 1.0; Partial = 0.5; Missing = 0.0.
* Explains the scoring methodology and clarifies that the score is an estimate, not an official ATS score.

### 3. Resume Customization and Comparison
* Tailors resume content to a target job description.
* Highlights relevant skills and experience supported by the source resume.
* Provides original-versus-customized bullet comparisons and evidence provenance.
* Displays match analysis to help identify supported, partially supported, and missing requirements.

### 4. ATS-Readable A4 PDF Export
* Generates downloadable A4 resume PDFs.
* Uses content-driven pagination and clean typography.
* Supports review of the customized resume before submission.

---

## Environment Variables

### Backend

Configure these in `backend/.env` for local development or in your hosting provider's environment settings for deployment.

| Variable | Purpose |
| :--- | :--- |
| `GEMINI_API_KEY` | Gemini API authentication |
| `GEMINI_MODEL` | Gemini model identifier |
| `CORS_ORIGINS` | Allowed frontend origins |
| `MAX_FILE_SIZE_MB` | Maximum upload size |
| `MAX_PAGES` | Maximum document page count |
| `MAX_RESUME_CHARS` | Maximum extracted resume characters |
| `MAX_JD_CHARS` | Maximum job-description characters |
| `LLM_TIMEOUT_SECONDS` | Language-model timeout configuration |

See `backend/.env.example` for the complete configuration and defaults.

### Frontend

| Variable | Purpose |
| :--- | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL |

For the deployed frontend, this points to the deployed backend. For local development, use `http://localhost:8000`.

---

## Deployment

* **Frontend:** Vercel
* **Backend:** Render
* **Frontend custom domain:** [resume.erprabhat.in](https://resume.erprabhat.in/)
* **Backend health endpoint:** [Check API health](https://resumecraft-api-xhor.onrender.com/api/v1/health)

Deployment configuration requires the frontend API URL and backend CORS origins to match the deployed domains.

---

## Security & Privacy

* Keep Gemini API keys on the backend.
* Never commit `.env`, `.env.local`, credentials, or private resume documents.
* Configure CORS to allow only the intended frontend origins.
* Avoid logging full resumes, job descriptions, or secrets.

---

## Disclaimer

ResumeCraft provides AI-assisted resume customization and an evidence-based match estimate. Its score is not an official ATS score and does not guarantee selection or an interview. Always review generated content for accuracy before submitting a resume.

---

## Author

**Prabhat Verma**
* **GitHub:** [Prabhat708](https://github.com/Prabhat708)
* **Project Repository:** [Resume-Customizer-AI](https://github.com/Prabhat708/Resume-Customizer-AI)
* **Live Application:** [resume.erprabhat.in](https://resume.erprabhat.in/)
