# Prism Setup Guide

This guide is written for beginners. Follow the steps in order.

## 1. Software Requirements

Install these before running Prism:

- Python 3.11 or newer
- Node.js 20 or newer
- npm
- Git
- Visual Studio Code, optional but recommended

Check versions:

```powershell
python --version
node --version
npm --version
git --version
```

## 2. Project Folder

Your project should look like this:

```text
prism/
  app/
  frontend/
  scripts/
  requirements.txt
  README.md
  docs/
```

The backend is in:

```text
app/
```

The frontend is in:

```text
frontend/
```

## 3. Clone Repository

```powershell
git clone <your-github-repository-url>
cd prism
```

If you already have the project locally, open the project root folder.

Example:

```powershell
cd C:\xl_venture
```

## 4. Backend Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

If knowledge-engine packages are not already included in `requirements.txt`, install:

```powershell
pip install chromadb==0.5.23 sentence-transformers==3.3.1 pypdf==5.1.0 python-docx==1.1.2
```

## 5. Backend Environment Variables

Create a file named `.env` in the project root.

Example:

```text
prism/.env
```

Add:

```env
PRISM_LLM_ENABLED=false
PRISM_LLM_PROVIDER=gemini
PRISM_LLM_MODEL=gemini-1.5-flash
GEMINI_API_KEY=
PRISM_LOG_LEVEL=INFO
PRISM_KNOWLEDGE_EMBEDDINGS=auto
```

### Running Without API Key

For the hackathon demo, Prism can run without an API key:

```env
PRISM_LLM_ENABLED=false
```

In this mode, Prism uses local fallback reasoning and seeded demo data.

### Running With Gemini API Key

To enable LLM-assisted context extraction and council reasoning:

```env
PRISM_LLM_ENABLED=true
PRISM_LLM_PROVIDER=gemini
PRISM_LLM_MODEL=gemini-1.5-flash
GEMINI_API_KEY=your_api_key_here
```

Use a Gemini model name available to your API key.

## 6. Start Backend

From the project root:

```powershell
uvicorn app.main:app --reload --port 8000
```

Expected output:

```text
Uvicorn running on http://127.0.0.1:8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

You should see the FastAPI Swagger page.

## 7. Frontend Setup

Open a second terminal.

```powershell
cd frontend
npm install --legacy-peer-deps
```

Create:

```text
frontend/.env.local
```

Add:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## 8. Start Frontend

From the `frontend` folder:

```powershell
npm run dev
```

Expected output:

```text
Ready
Local: http://localhost:3000
```

Open:

```text
http://localhost:3000/dashboard
```

## 9. Verification Checklist

Use this checklist before recording the demo.

- Backend runs on `http://127.0.0.1:8000`
- FastAPI docs open at `http://127.0.0.1:8000/docs`
- Frontend runs on `http://localhost:3000`
- Dashboard opens correctly
- Decisions page opens correctly
- New decision can be created
- Create and Run Council works
- Executive Council page shows agent discussion
- Evidence page shows evidence packets
- Analysis page shows scenario/risk information
- Recommendation page shows final action
- Approve, Reject, and Request Changes buttons show confirmation
- Outcome recording works
- Analytics page loads

## 10. Common Errors and Fixes

### Error: `ModuleNotFoundError: No module named 'app'`

Cause: backend command was run from the wrong folder, or the `app` folder is missing.

Fix:

```powershell
cd C:\xl_venture
uvicorn app.main:app --reload --port 8000
```

Make sure this exists:

```text
C:\xl_venture\app
```

### Error: `Could not read package.json`

Cause: `npm install` was run from the wrong folder.

Fix:

```powershell
cd C:\xl_venture\frontend
npm install --legacy-peer-deps
```

Make sure this exists:

```text
C:\xl_venture\frontend\package.json
```

### Error: `next.config.ts is not supported`

Cause: Next.js is reading an unsupported config file.

Fix:

```powershell
cd C:\xl_venture\frontend
del .\next.config.ts
```

The frontend should use:

```text
next.config.mjs
```

### Error: Frontend says `Failed to fetch`

Cause: backend is not running or frontend API URL is wrong.

Fix:

1. Start backend:

```powershell
cd C:\xl_venture
uvicorn app.main:app --reload --port 8000
```

2. Check `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

3. Restart frontend:

```powershell
cd C:\xl_venture\frontend
npm run dev
```

### Error: `ERESOLVE unable to resolve dependency tree`

Cause: npm dependency conflict.

Fix:

```powershell
npm install --legacy-peer-deps
```

### Error: LLM unavailable

Cause: LLM is disabled or API key/model is missing.

Fix for demo mode:

```env
PRISM_LLM_ENABLED=false
```

Fix for LLM mode:

```env
PRISM_LLM_ENABLED=true
PRISM_LLM_MODEL=gemini-1.5-flash
GEMINI_API_KEY=your_api_key_here
```

## 11. Demo Run Order

1. Start backend.
2. Start frontend.
3. Open Dashboard.
4. Go to Decisions.
5. Create a decision.
6. Click Create and Run Council.
7. Open the decision card.
8. Show Executive Council.
9. Show Evidence.
10. Show Analysis.
11. Show Recommendation.
12. Approve the decision.
13. Record outcome.
14. Show learning/outcomes.

## 12. Final Submission Check

Before submitting:

- Push source code to GitHub.
- Include `README.md`.
- Include `docs/setup-guide.md`.
- Include `docs/architecture.md`.
- Add demo video link.
- Add architecture walkthrough video link.
- Check that setup commands work from a fresh clone.
