# Prism Workspace UI

Frontend-only navigation and information architecture upgrade.

This keeps the existing backend APIs and business logic intact.

## What Changed

- Workspace sidebar with separate routes
- Dashboard overview page
- Decisions list page
- Decision details page with only Overview and Recommendation tabs
- Executive Council workspace
- Evidence workspace
- Analysis workspace
- Outcomes workspace
- Analytics workspace
- Integrations and Settings pages
- Guided demo path for new users
- Action popups after approve, reject, request changes, and outcome recording
- Clear Refresh data wording instead of unclear sync behavior
- Create Decision form appears only on Decisions page
- Review buttons lock after one human choice is saved
- Decision details no longer has an Activity tab
- Prism product mark replaces the generic sparkle icon

## Copy Into Your Frontend

```powershell
cd C:\xl_venture\frontend
Remove-Item .\app, .\components, .\lib, .\types -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item .\next.config.ts -Force -ErrorAction SilentlyContinue

cd C:\xl_venture
Copy-Item "C:\Users\immad\Documents\Codex\2026-06-26\introduction-every-interaction-inside-decisionos-is\outputs\prism-workspace-ui\*" ".\frontend\" -Recurse -Force
```

If npm packages are already installed, run:

```powershell
cd C:\xl_venture\frontend
npm run dev
```

If packages are missing, run:

```powershell
cd C:\xl_venture\frontend
npm install --legacy-peer-deps
npm run dev
```

Backend should still run separately:

```powershell
cd C:\xl_venture
uvicorn app.main:app --reload --port 8000
```

Open:

```text
http://localhost:3000/dashboard
```
