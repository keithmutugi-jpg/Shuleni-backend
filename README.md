# Shuleni Backend

Django REST API backend for Shuleni — an online school management platform.

## What this covers

- Multi-tenant school registration (each school's data is fully isolated)
- Member accounts: owners, educators, and students
- Token-based authentication
- Adding students/educators with auto-generated login credentials.

## Setup

```bash
python -m venv venv
venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Runs on `http://localhost:8000` by default.

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/health/` | GET | Health check |
| `/api/register-school/` | POST | Create a new school + owner account |
| `/api/login/` | POST | Log in with school name/ID, username, password |
| `/api/logout/` | POST | Invalidate the current token |
| `/api/session/` | GET | Get the current logged-in user |
| `/api/users/` | GET, POST | List school members / add a student or educator |