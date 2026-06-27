# Backend Day 2 Patch

Your backend needs CORS so the Next.js frontend can call it from `localhost:3000`.

Open:

```text
C:\xl_venture\app\main.py
```

Add this import near the top:

```python
from fastapi.middleware.cors import CORSMiddleware
```

After `app = FastAPI(...)`, add:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then restart backend:

```powershell
uvicorn app.main:app --reload --port 8000
```

