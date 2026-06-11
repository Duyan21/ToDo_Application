# Todo Application

> A self-hosted, deadline-aware task management web app with automatic real-time notifications.

---

## Overview

**Todo Application** is a multi-user web application for personal task management. Users can create tasks with deadlines, set per-task reminder windows, and receive automatic in-app notifications — no manual refresh required.

Most lightweight todo tools are passive: they store tasks but never surface them again. This app solves that by running a background scheduler that continuously monitors deadlines and pushes alerts into each user's notification feed. A task approaching its deadline triggers a **REMINDER**; a task that has passed its deadline is escalated to **OVERDUE**. Completing the task clears all its notifications automatically.

The project was developed as a Python web programming course assignment at the **University of Information Technology (UIT)**, Semester 2 — 2025/2026.

---

## Key Features

- **Task CRUD** — create, edit, complete, and delete tasks with title, description, deadline, and priority
- **Deadline reminders** — configurable reminder window per task (e.g. notify 30 minutes before deadline)
- **Automatic notifications** — background scheduler fires every 3 seconds; no polling from the client required
- **Overdue escalation** — REMINDER notifications are automatically replaced by OVERDUE when a deadline passes
- **Bulk CSV import** — upload a `.csv` file to create multiple tasks at once
- **Session-based authentication** — email + password registration and login
- **Task filtering** — view all, pending-only, or completed-only tasks
- **Responsive UI** — Bootstrap-based, works on desktop and mobile

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Web framework | Flask 3.1 |
| ORM | SQLAlchemy 2.0 + Flask-SQLAlchemy 3.1 |
| Database | SQL Server (production) / SQLite (development fallback) |
| Background jobs | APScheduler 3.11 |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap |
| Auth | Flask sessions + Werkzeug password hashing |
| Testing | pytest + pytest-cov |
| Linting | flake8 + ruff |
| CI/CD | GitHub Actions |

---

## Architecture

The application is structured in four horizontal layers. Each layer depends only on the layer below it.

```
HTTP Request
     │
     ▼
┌─────────────┐
│   Routes    │  Input validation, session checks, HTTP responses
└──────┬──────┘
       │
┌──────▼──────┐
│  Services   │  Business logic, orchestration
└──────┬──────┘
       │
┌──────▼──────┐
│Repositories │  All database queries, no business logic
└──────┬──────┘
       │
┌──────▼──────┐
│   Models    │  SQLAlchemy ORM definitions
└─────────────┘
```

**DTOs** (`src/dto/`) decouple the database models from API responses — services accept and return DTOs, never raw ORM objects.

**Custom decorators** (`src/utils/decorators/`) handle cross-cutting concerns: `@require_auth` guards routes, `@validate_input` enforces field rules, `@check_execution_time` measures route latency.

### Notification pipeline

```
Task saved with deadline
         │
         ▼
  APScheduler — every 3 s
         │
  ┌──────┴────────────────────────────────┐
  │                                       │
deadline − reminder_minutes ≤ now    deadline < now
         │                                │
  REMINDER created               OVERDUE created
  (OVERDUE removed if exists)    (REMINDER removed if exists)
         │                                │
         └──────────────┬────────────────┘
                        │
               task marked complete
                        │
               all notifications deleted
```

### Database schema

| Table | Key columns |
|---|---|
| `Users` | `id`, `email` (unique), `password_hash`, `created_at` |
| `Tasks` | `id`, `user_id`, `title`, `deadline`, `priority`, `status`, `reminder_minutes` |
| `Notifications` | `id`, `task_id`, `user_id`, `type` (REMINDER / OVERDUE), `is_read` |
| `Files` | `id`, `user_id`, `filename`, `file_path`, `is_imported` |

Indexed columns: `Tasks.user_id`, `Tasks.deadline`, `Tasks.is_done`, `Notifications.task_id`, `Notifications.user_id`.

---

## Project Structure

```
todo_app/
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions: lint → test
├── src/
│   ├── app/
│   │   └── app.py                     # Flask application factory
│   ├── common/
│   │   └── errors.py                  # Domain exceptions (AuthError, etc.)
│   ├── database/
│   │   ├── models.py                  # SQLAlchemy ORM models
│   │   └── schema.sql                 # SQL Server DDL script
│   ├── dto/
│   │   ├── file_dto.py
│   │   ├── notification_dto.py
│   │   ├── task_dto.py
│   │   └── user_dto.py
│   ├── repositories/
│   │   ├── base_repository.py
│   │   ├── file_repository.py
│   │   ├── notification_repository.py
│   │   ├── task_repository.py
│   │   └── user_repository.py
│   ├── routes/
│   │   ├── auth.py                    # /api/register  /api/signin  /api/logout
│   │   ├── home.py                    # / home page
│   │   ├── notification.py            # /notifications/*
│   │   └── task.py                    # /tasks/*
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── file_service.py
│   │   ├── notification_service.py    # Background deadline checker
│   │   └── task_service.py
│   ├── static/                        # CSS + JS assets
│   ├── templates/                     # Jinja2 HTML templates
│   ├── tests/
│   │   ├── conftest.py                # Fixtures — in-memory SQLite, test client
│   │   ├── test_auth.py
│   │   ├── test_dto.py
│   │   ├── test_notifications.py
│   │   └── test_tasks.py
│   └── utils/
│       ├── decorators/
│       │   ├── check_execution_time.py
│       │   ├── logging.py
│       │   ├── require_auth.py
│       │   └── validate_input.py
│       └── generators/
│           └── read_csv.py
├── upload/                            # Runtime directory for uploaded CSV files
├── .env.example
├── main.py
├── pytest.ini
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- A modern web browser
- *(Optional)* SQL Server + ODBC Driver 17 or 18 for production use

---

### Option A — SQLite (quickest, no database install)

SQLite is used automatically when SQL Server environment variables are absent. Recommended for development and evaluation.

```bash
# 1. Clone
git clone https://github.com/Duyan21/ToDo_Application.git
cd todo_app

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Open .env and set a SECRET_KEY. Leave DB_* lines commented out.

# 5. Run
python main.py
```

Open `http://localhost:5000` in your browser.

---

### Option B — SQL Server

```bash
# Additional driver
pip install pyodbc
```

**Create the database**

Open SQL Server Management Studio and execute `src/database/schema.sql`.  
This creates the `todo_app_db` database and all required tables.

**Configure `.env`**

```bash
cp .env.example .env
```

Uncomment and fill in the block that matches your SQL Server edition:

```dotenv
SECRET_KEY=replace-with-a-secure-random-value

# SQL Server Express (default local install)
DB_HOST=localhost\SQLEXPRESS
DB_NAME=todo_app_db
DB_DRIVER=ODBC Driver 17 for SQL Server

# SQL Server Standard / Default instance
# DB_HOST=localhost
# DB_NAME=todo_app_db
# DB_DRIVER=ODBC Driver 17 for SQL Server

# Named instance (e.g. SQL Server 2019)
# DB_HOST=localhost\SQL2019
# DB_NAME=todo_app_db
# DB_DRIVER=ODBC Driver 18 for SQL Server
```

```bash
python main.py
```

**Connection troubleshooting**

| Error | Likely cause | Fix |
|---|---|---|
| `Login failed` | SQL Server not running | Start the SQL Server service |
| `ODBC driver not found` | Driver name mismatch | Check `odbcad32.exe` → System DSN for the exact name |
| TCP connection timeout | TCP/IP not enabled | Enable TCP/IP in SQL Server Configuration Manager |
| Firewall block | Windows Firewall | Allow port 1433 for SQL Server |

---

## Usage Guide

### First run

1. Navigate to `http://localhost:5000`
2. Click **Register** and create an account
3. You are redirected to the task list after registration

### Creating a task

1. Click **Add Task**
2. Fill in: title (required), description, deadline, priority, and reminder window
3. Save — the task appears in your list immediately

### Notifications

Notifications appear in the top-right bell icon. No page refresh is needed.

| Notification type | When it appears |
|---|---|
| **REMINDER** | `now >= deadline − reminder_minutes` |
| **OVERDUE** | `now > deadline` (replaces REMINDER) |
| *(cleared)* | Task is marked complete |

### Bulk CSV import

1. Go to **Import** (`/tasks/import`)
2. Download the sample CSV to see the expected format
3. Upload your filled-in CSV
4. Click **Run Import** — tasks are created and the file is marked as imported

---

## API Reference

All write endpoints accept and return JSON. Page routes return HTML.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/register` | Create a new account |
| `POST` | `/api/signin` | Sign in; starts a session |
| `POST` | `/api/logout` | Invalidate the current session |

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/tasks` | Task list page |
| `POST` | `/tasks` | Create a task |
| `PUT` | `/tasks/<id>/edit` | Update task fields |
| `PUT` | `/tasks/<id>/complete` | Mark as complete |
| `PUT` | `/tasks/<id>/uncomplete` | Revert to pending |
| `DELETE` | `/tasks/<id>/delete` | Delete a task |

### CSV Import

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/tasks/import` | Import page |
| `GET` | `/tasks/import/download-sample` | Download sample CSV |
| `POST` | `/tasks/upload` | Upload a CSV file |
| `POST` | `/tasks/import-run/<id>` | Execute import from uploaded file |

### Notifications

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/notifications` | Get all notifications |
| `POST` | `/notifications/<id>/read` | Mark one notification as read |
| `POST` | `/notifications/read-all` | Mark all as read |
| `POST` | `/notifications/clear` | Delete all notifications |

---

## Testing

Tests run against an in-memory SQLite database — no SQL Server required.

```bash
# Run the full suite
pytest

# With coverage report
pytest --cov=src --cov-report=term-missing

# Single file
pytest src/tests/test_auth.py -v
```

141 test cases across 4 files:

| File | Covers |
|---|---|
| `test_auth.py` | Register / sign-in / logout routes and AuthService |
| `test_tasks.py` | Task CRUD routes, service filters, ownership checks |
| `test_notifications.py` | Notification routes and background sync logic |
| `test_dto.py` | DTO serialization and field validation |

---

## Code Quality & CI

### Linting

```bash
# flake8 — PEP 8, max line length 120
flake8 src/ --exclude=src/tests --max-line-length=120 --extend-ignore=E203,W503

# ruff — additional fast checks
ruff check src/ --exclude src/tests --line-length 120
```

### CI pipeline (GitHub Actions)

Runs automatically on every push and pull request to `main` or `develop`.

| Job | Steps | Condition |
|---|---|---|
| **lint** | flake8 → ruff | always |
| **test** | pytest + coverage ≥ 60% | after lint passes |

A pull request cannot be merged if either job fails.

```bash
# Reproduce CI locally (all tools are in requirements.txt)
flake8 src/ --exclude=src/tests --max-line-length=120 --extend-ignore=E203,W503
pytest --cov=src --cov-report=term-missing --cov-fail-under=60
```
