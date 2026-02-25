# Voltask API

A production-ready **multi-tenant SaaS Task Manager** built with **FastAPI** + **PostgreSQL (Supabase)**.

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | Supabase PostgreSQL direct connection URL |
| `SECRET_KEY` | Long random string for JWT signing |
| `ALGORITHM` | `HS256` (default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes (default: 30) |

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

Visit **http://127.0.0.1:8000/docs** for the interactive Swagger UI.

---

## 📁 Project Structure

```
app/
├── main.py
├── core/
│   ├── config.py        # Pydantic settings from .env
│   └── security.py      # JWT + bcrypt
├── db/
│   ├── base.py          # SQLAlchemy declarative base
│   └── session.py       # Engine + get_db dependency
├── models/
│   ├── company.py
│   ├── user.py          # Roles: admin / manager / employee
│   ├── task.py          # Status: pending / in-progress / completed
│   └── otp.py           # Password reset OTPs (5-min TTL)
├── schemas/
│   ├── auth.py
│   ├── user.py
│   └── task.py
├── routers/
│   ├── auth.py          # /auth/*
│   ├── users.py         # /users/*
│   └── tasks.py         # /tasks/*
├── services/
│   ├── auth_service.py
│   └── task_service.py
└── dependencies/
    ├── auth.py          # get_current_user (JWT decode)
    └── role.py          # require_roles(*roles) RBAC factory
```

---

## 🔑 API Endpoints

### Auth (`/auth`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Create company + admin |
| POST | `/auth/login` | — | Get JWT token |
| GET | `/auth/me` | 🔒 | Current user info |
| POST | `/auth/forgot-password` | — | Generate OTP |
| POST | `/auth/reset-password` | — | Reset with OTP |

### Users (`/users`) — Admin only

| Method | Path | Description |
|--------|------|-------------|
| POST | `/users/invite` | Invite user to company |
| GET | `/users/` | List all company users |
| PATCH | `/users/{id}/deactivate` | Deactivate a user |

### Tasks (`/tasks`)

| Method | Path | Who | Description |
|--------|------|-----|-------------|
| POST | `/tasks/` | Admin, Manager | Create task |
| GET | `/tasks/` | All | Filtered by role |
| PATCH | `/tasks/{id}` | Role-based | Update task |
| PATCH | `/tasks/{id}/assign` | Admin, Manager | Assign task |
| DELETE | `/tasks/{id}` | Admin | Delete task |

**Query params for `GET /tasks/`:** `skip`, `limit`, `search` (title search)

---

## 🔐 Security

- All routes except `register` and `login` require `Authorization: Bearer <token>`
- Every DB query filters by `company_id` for tenant isolation
- Passwords hashed with **bcrypt**
- OTPs expire after **5 minutes** and are single-use
- JWT payload contains `user_id`, `company_id`, and `role`

---

## 🧪 Testing with Swagger

1. `POST /auth/register` → get your admin user
2. `POST /auth/login` → copy the `access_token`
3. Click **Authorize** in Swagger → paste token
4. Try all protected endpoints!
