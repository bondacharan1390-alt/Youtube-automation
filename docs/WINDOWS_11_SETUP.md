# Windows 11 Setup Guide

## Requirements

- Python 3.11.
- Node.js LTS.
- 8 GB RAM minimum.
- 10 GB free disk minimum.
- Optional NVIDIA GPU with current Windows drivers.

## Backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy ..\.env.example ..\.env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

The development token endpoint is enabled only when `DEBUG=true` and `APP_ENV` is not production.
