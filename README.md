# AI YouTube Automation Studio

This project contains a FastAPI/SQLite backend and a Next.js frontend for generating,
reviewing, and optionally publishing YouTube videos on Windows 11.

## Setup

### Backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example ..\.env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The SQLite database is initialized automatically. Alembic migrations are in
`backend/alembic/versions`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The default development login is seeded as
`creator@youtube-studio.ai` / `creator12345`.

## Phase 7 Automation

Open **Automation** in the sidebar. Select a project, start the workflow, and use
pause, resume, cancel, retry, and individual task regeneration controls. The live
timeline refreshes automatically.

The pipeline executes research, script, storyboard, voice, images, subtitles,
video rendering, editing, thumbnail, SEO metadata, quality check, explicit approval,
and upload in dependency order. Heavy tasks use a sequential hardware guard.

## Publishing Safety

- Publishing always requires an explicit approval request.
- Private is the default privacy setting.
- Public publishing requires both quality-check success and explicit public confirmation.
- The final MP4, thumbnail, title, description, and privacy setting are reviewed before upload.
- An upload is not reported as successful until the YouTube integration confirms a video ID.
- A successful upload and YouTube video ID prevent repeat upload execution through idempotency records.

Scheduled publishing accepts a timezone-aware date/time. The application validates future
times and keeps scheduled jobs in persistent SQLite state. YouTube API credentials and quota
determine real delivery; offline/staging runs use the existing simulated uploader.

## Optional n8n

n8n is disabled by default and is not required to run the application.

1. Set `N8N_ENABLED=true` and `N8N_WEBHOOK_SECRET` to a long random value.
2. In n8n, create a webhook that sends `project_id`, optional `settings`, and an optional
   `idempotency_key`.
3. Add header `X-N8n-Secret` containing the same secret.
4. POST to `http://localhost:8000/api/v1/automation/n8n/webhook`.

The endpoint refuses disabled integrations and rejects invalid secrets. Idempotency keys
prevent duplicate workflow creation and execution.

## Hardware

The automation worker processes resource-intensive tasks sequentially and limits concurrent
rendering through the hardware queue. On low-memory Windows hosts it triggers garbage
collection and exposes hardware status through the existing stats/provider APIs.

## YouTube Analytics

Live channel totals and historical reports require Google OAuth credentials plus the
`https://www.googleapis.com/auth/yt-analytics.readonly` scope. Configure
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI`, or the
equivalent `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and
`YOUTUBE_REDIRECT_URI` variables.

Historical data is stored only after the YouTube Analytics API returns a live report.
The analytics page and exports never use demo totals as live data. If credentials,
channel authorization, or an Analytics report are unavailable, the API returns an
explicit pending, permission, or availability status.

## Testing

```powershell
cd backend
$env:PYTHONPATH="."
.\.venv\Scripts\pytest.exe -q
```

```powershell
cd frontend
npm.cmd run build
```
