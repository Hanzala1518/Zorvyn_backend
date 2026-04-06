# Finance Dashboard

> Full-stack finance management system with role-based access control,
> real-time analytics, audit logging, and CSV export.

## Tech Stack

| Layer    | Technology                              |
|----------|-----------------------------------------|
| Frontend | Next.js 14, TypeScript, Tailwind, shadcn/ui, Recharts |
| Backend  | FastAPI (Python 3.11+), Pydantic v2, python-jose |
| Database | Supabase (PostgreSQL)                   |
| Auth     | Custom JWT + RBAC middleware            |

## Role Permissions

| Feature              | Viewer | Analyst | Admin |
|----------------------|--------|---------|-------|
| View dashboard       | ✅     | ✅      | ✅    |
| View transactions    | ✅     | ✅      | ✅    |
| Create transactions  | ❌     | ✅      | ✅    |
| Edit transactions    | ❌     | ✅      | ✅    |
| Export CSV           | ❌     | ✅      | ✅    |
| Delete transactions  | ❌     | ❌      | ✅    |
| Manage users         | ❌     | ❌      | ✅    |
| View audit logs      | ❌     | ❌      | ✅    |

## Project Structure

```
finance-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, router registration
│   │   ├── config.py          # Pydantic settings from .env
│   │   ├── dependencies.py    # JWT auth, role guards, Supabase clients
│   │   ├── routers/           # auth, users, transactions, dashboard
│   │   ├── services/          # business logic layer
│   │   └── schemas/           # Pydantic request/response models
│   └── requirements.txt
└── frontend/
    ├── app/
    │   ├── login/page.tsx
    │   ├── dashboard/
    │   │   ├── layout.tsx     # sidebar navigation
    │   │   └── page.tsx       # KPI cards + charts
    │   ├── transactions/page.tsx
    │   └── users/page.tsx
    └── lib/
        ├── api.ts             # axios instance + typed API calls
        └── auth.ts            # localStorage token helpers
```

## Step 1 — Supabase Setup

1. Go to https://supabase.com → **New Project** → choose a name and strong DB password
2. Wait ~2 minutes for provisioning
3. In left sidebar → **Settings → API**, copy:
   - **Project URL** → this is your `SUPABASE_URL`
   - **anon / public** key → `SUPABASE_KEY`
   - **service_role** key → `SUPABASE_SERVICE_KEY` (keep this secret!)
4. In left sidebar → **SQL Editor → New Query**
5. Paste the entire contents of `SUPABASE_SETUP.sql`
6. Click **Run** (green button, top right)
7. Verify in **Table Editor**: you should see `users`, `transactions`, `categories`, `audit_logs`
8. Check **users** table has 3 rows (admin, analyst, viewer)

## Step 2 — Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Open .env and fill in your values:
#   SUPABASE_URL=https://xxxx.supabase.co
#   SUPABASE_KEY=eyJ...
#   SUPABASE_SERVICE_KEY=eyJ...
#   JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Start the server
uvicorn app.main:app --reload --port 8000
```

✅ Backend: http://localhost:8000  
✅ API Docs (Swagger): http://localhost:8000/docs  
✅ Health check: http://localhost:8000/health

## Step 3 — Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
# .env.local already has: NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

✅ Frontend: http://localhost:3000

## Demo Credentials

| Role    | Email              | Password    |
|---------|--------------------|-------------|
| Admin   | admin@demo.com     | admin123    |
| Analyst | analyst@demo.com   | analyst123  |
| Viewer  | viewer@demo.com    | viewer123   |

## API Reference

| Method | Endpoint                          | Role     | Description             |
|--------|-----------------------------------|----------|-------------------------|
| POST   | /api/auth/login                   | Public   | Login, get JWT token    |
| GET    | /api/auth/me                      | Any      | Current user info       |
| GET    | /api/transactions                 | Viewer+  | List with filters       |
| POST   | /api/transactions                 | Analyst+ | Create transaction      |
| GET    | /api/transactions/export          | Analyst+ | Download CSV            |
| PATCH  | /api/transactions/{id}            | Analyst+ | Update transaction      |
| DELETE | /api/transactions/{id}            | Admin    | Soft delete             |
| GET    | /api/dashboard/summary            | Viewer+  | KPI totals              |
| GET    | /api/dashboard/monthly-trends     | Viewer+  | Monthly chart data      |
| GET    | /api/dashboard/category-breakdown | Viewer+  | Category pie chart data |
| GET    | /api/dashboard/weekly-trends      | Viewer+  | Weekly chart data       |
| GET    | /api/dashboard/recent-activity    | Viewer+  | Last N transactions     |
| GET    | /api/dashboard/audit-logs         | Admin    | Action history          |
| GET    | /api/users                        | Admin    | List users              |
| POST   | /api/users                        | Admin    | Create user             |
| PATCH  | /api/users/{id}                   | Admin    | Update role/status      |
| DELETE | /api/users/{id}                   | Admin    | Soft delete user        |

Full interactive docs with request/response schemas: **http://localhost:8000/docs**

## Design Decisions

1. **Custom JWT over Supabase Auth** — gives full control over the token payload (role embedding)
   and keeps auth logic entirely in FastAPI where RBAC middleware can inspect it cleanly.
2. **Soft deletes everywhere** — `is_deleted=true` preserves audit integrity; deleted records
   remain in the database for compliance, just filtered from normal queries.
3. **Service layer separation** — routers contain only HTTP concerns (parsing, responses, status
   codes); all business logic lives in services. This makes logic testable without HTTP context.
4. **Audit log on every write** — every create/update/delete writes a record to `audit_logs`
   with the acting user's ID and a details JSONB blob. Admins can see a full action history.
5. **Partial indexes on Supabase** — indexes on `transactions` include `WHERE is_deleted = FALSE`
   so soft-deleted rows don't inflate index size or slow down live queries.
6. **30s in-memory cache on summary** — the dashboard KPI summary is the most-read endpoint.
   A simple time-based dict cache reduces repeated identical DB reads in quick succession.
7. **CSV export as streaming response** — built in-memory using Python's `csv` module,
   returned as `StreamingResponse` so no temp files are created on the server.
