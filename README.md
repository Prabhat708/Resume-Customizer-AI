# ResumeCraft — AI Resume Customizer

An ATS-aligned, factuality-preserving resume customizer built with Next.js, FastAPI, and Google Gemini. Tailors resumes to target job descriptions, computes deterministic evidence match scores, visualizes side-by-side bullet diffs with source provenance, and exports ATS-readable, publication-grade A4 PDFs.

---

## Architecture Overview

- **Frontend (`/frontend`)**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Lucide icons.
- **Backend (`/backend`)**: FastAPI, Pydantic v2, Google Gemini API, PyMuPDF (`fitz`), `python-docx`, ReportLab.
- **Factuality & Provenance Engine**: Verifies that every customized bullet maps to verified source achievements. Rejects metric fabrication, skill hallucination, and unsupported employment claims.

---

## Prerequisites

- **Python 3.11+** (tested on Python 3.11 - 3.13)
- **Node.js 18+** (Node 20+ recommended) and `npm`
- **Google Gemini API Key** (for live AI tailoring)

---

## Quickstart Setup

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and supply your GEMINI_API_KEY:
# GEMINI_API_KEY=your_key_here
# GEMINI_MODEL=gemini-2.5-flash

# Run the backend API server (runs on http://127.0.0.1:8000)
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables (defaults to http://localhost:8000)
cp .env.example .env.local

# Run the development server (runs on http://localhost:3000)
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) in your browser.

---

## Running Verification & Tests

### Backend Automated Test Suite (102 Tests)

```bash
cd backend
.\.venv\Scripts\pytest -v
```

Covers:
- Document parser (PDF/DOCX magic byte validation, corruption, encryption, extraction)
- Factuality auditor (metric containment, skill retention, provenance tracking, fallback handling)
- Scoring arithmetic (weighted calculation, rounding boundaries, empty requirements)
- PDF exporter (ReportLab A4 layout, zero-footer verification, special characters, long URLs)
- Browser print pagination (2-page headless layout verification)

### Frontend Lint and Production Build

```bash
cd frontend
npm run lint
npm run build
```

---

## Core Capabilities & Engineering Highlights

1. **Factuality Guarantee**:
   - Skills can only be highlighted if present in the original resume.
   - Customized bullets retain strict link to `source_bullet_id`.
   - Any metric or numeral not in the original text triggers an explicit auditor warning.
2. **Deterministic Match Scoring**:
   - Scores are computed via a backend mathematical formula (Required: 1.5×, Preferred: 1.0×; Full evidence: 1.0, Partial: 0.5, Missing: 0.0).
   - Never hallucinates scores; displays transparent methodology and ATS disclaimer.
3. **Calibrated Evidence Separation**:
   - Clearly distinguishes between primary employment evidence and personal/project evidence.
   - Explains zero-weight informational requirements to prevent double-penalizing score arithmetic.
4. **Publication-Grade A4 PDF Export**:
   - Content-driven dynamic pagination using ReportLab and A4 dimensions.
   - ATS-optimized layout with clean typography, proper page balance, and zero footers.
