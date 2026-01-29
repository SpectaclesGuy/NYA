# NYA Platform

NYA is a private community platform built with FastAPI and MongoDB. The frontend is served as static HTML from `Pages/`.

## Overview
- FastAPI backend with cookie-based auth
- Static HTML/CSS/JS frontend
- MongoDB persistence (Motor)
- Role-based onboarding and dashboards
- Email notifications via SMTP (optional)

## Requirements
- Python 3.11+
- MongoDB (local or hosted)

## Quick Start
1) Create and activate a virtual environment
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies
```
pip install -r requirements.txt
```

3) Create a `.env` file (minimal keys)
```
NYA_MONGODB_URI=...
NYA_MONGODB_DB=...
NYA_JWT_SECRET=...
NYA_GOOGLE_CLIENT_ID=...
NYA_GOOGLE_CLIENT_SECRET=...
NYA_FRONTEND_ORIGIN=...
NYA_DEV_LOGIN_ENABLED=false
NYA_ALLOW_ALL_DOMAINS=false
```

4) Run the server
```
uvicorn app.main:app --reload
```

## Scripts
- Seed data: `python scripts\seed.py`
- Reset data: `python scripts\reset_db.py`

## Notes
- Auth, onboarding, and role access are enforced server-side.
- SMTP is optional and controlled via environment variables.
- Static assets are served from `/assets`.

for logs
sudo docker compose logs -f app
sudo ufw deny from 79.124.40.174