# Shuleni Backend

Django REST API backend for Shuleni — an online school management platform.

## What this covers

- Multi-tenant school registration (each school's data is fully isolated)
- Member accounts: owners, educators, and students
- Token-based authentication
- Adding students/educators with auto-generated login credentials.
- Shared resources, exams/results, attendance and class chats with school-level isolation.
- Multipart resource uploads and secure server-side exam grading.

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
| `/api/schools/register/` | POST | Create a new school + owner account |
| `/api/auth/login/` | POST | Log in with school name/ID, username, password |
| `/api/auth/logout/` | POST | Invalidate the current token |
| `/api/auth/session/` | GET | Get the current logged-in user |
| `/api/users/` | GET, POST | List school members / add a student or educator |
| `/api/resources/` | GET, POST | List/upload school resources |
| `/api/exams/` | GET, POST | List/create exams |
| `/api/exams/<id>/submit/` | POST | Submit and server-grade a student attempt |
| `/api/exam-results/` | GET | Student or staff exam results |
| `/api/attendance/` | GET | School attendance records |
| `/api/attendance/submit/` | POST | Educator/owner attendance sign-off |
| `/api/chats/` | GET | School/class chat rooms |
| `/api/chats/<id>/messages/` | POST | Send a class chat message |