# NYA Backend + Web UI

NYA (Not Your Average) is a private, university-restricted community platform built with FastAPI and MongoDB (Motor). The frontend is served as static HTML pages from the `Pages/` folder.

## Requirements
- Python 3.11
- MongoDB (Atlas or local)

## Setup
1) Create and activate a virtual environment.
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies.
```
pip install -r requirements.txt
```

3) Create a `.env` file in the project root (example keys).
```
MONGODB_URI=your_mongo_uri
MONGODB_DB=nya
NYA_GOOGLE_CLIENT_ID=your_google_client_id
NYA_GOOGLE_CLIENT_SECRET=your_google_client_secret
NYA_GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
JWT_SECRET_KEY=your_secret
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=60
SESSION_COOKIE_NAME=ynot_session
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_SAMESITE=lax
DEV_LOGIN_ENABLED=True
```

Note: The OAuth client must allow `http://localhost:8000` as an authorized origin for Google Sign-In.

## Run
Start the API server:
```
uvicorn app.main:app --reload
```

Open the app:
- Authentication: `http://localhost:8000/authentication`

## App Flow
1) User signs in with Google.
2) A transition screen plays for ~3 seconds.
3) User is routed to role selection, setup, or dashboard based on onboarding status.

## Pages
- `/authentication` - Google sign-in
- `/transition` - animation splash after login
- `/onboarding/role` - role selection
- `/profile/setup` - user profile setup
- `/mentor/setup` - mentor profile setup
- `/mentor/pending` - mentor approval pending
- `/dashboard` - user dashboard
- `/mentors` - mentor discovery
- `/requests` - incoming/outgoing requests + team members
- `/mentor/dashboard` - mentor request inbox
- `/admin/users` - admin users panel
- `/admin/mentors` - admin mentor approvals

## API (Prefix `/api`)
- Auth: `POST /auth/google/login`, `POST /auth/refresh`, `POST /auth/logout`
- Config: `GET /config`
- Users: `GET /users/me`, `GET /users/discover`, `GET /users/recommended`
- Profiles: `GET /profiles/{user_id}`, `GET/POST /profiles/me`
- Mentors: `GET /mentors`, `GET /mentors/{mentor_id}`, `GET/POST /mentors/me`
- Requests: `POST /requests`, `GET /requests/incoming`, `GET /requests/outgoing`, `POST /requests/{id}/accept`, `POST /requests/{id}/reject`
- Onboarding: `GET /onboarding/status`, `POST /onboarding/role`
- Admin: `GET /admin/users`, `POST /admin/users/{user_id}/action`, `GET /admin/mentors/pending`, `POST /admin/mentors/{mentor_id}/approve`, `POST /admin/mentors/{mentor_id}/reject`

## Seed Data (Optional)
Populate sample data:
```
python scripts\\seed.py
```

Reset the database:
```
python scripts\\reset_db.py
```

## Static Assets
- Logos: `/assets/nya_logo.png`, `/assets/nya_logo_nobg.png`
- Animation: `/assets/animation1.mp4`

## Notes
- Only `@thapar.edu` emails are allowed.
- Mentor profiles are hidden until admin approval.
- Email is revealed only after a request is accepted.
