# DecisionOS Day 2 Frontend

This is the Day 2 frontend implementation for the DecisionOS hackathon prototype.

It connects to the Day 1 FastAPI backend and turns the backend Decision Card into a polished enterprise dashboard.

## What This Implements

- DecisionOS dashboard
- Create and run demo Decision
- Planner execution view
- Decision lifecycle timeline
- Decision Council agent cards
- Recommendation card
- Simulation alternatives
- Evidence and memory panels
- Human review actions
- Outcome learning action

## Required Backend

Run your backend first from `C:\xl_venture`:

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

## Frontend Setup

From `C:\xl_venture`:

```powershell
npx create-next-app@latest frontend --ts --tailwind --eslint --app
```

Then copy the files from this folder into `C:\xl_venture\frontend`.

Install required frontend package:

```powershell
cd frontend
npm install lucide-react
```

Create `.env.local`:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Run:

```powershell
npm run dev
```

Open:

```text
http://localhost:3000
```

## Demo Flow

1. Click `Run Decision Council`
2. Show Planner selected agents
3. Show Decision Council outputs
4. Show recommendation: `Schedule executive value workshop`
5. Click `Approve`
6. Click `Record Renewed Outcome`
7. Explain that the completed Decision becomes memory

