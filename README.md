# Pennywise — Personal Expense Tracker

A responsive expense tracker with a Flask JSON API and React/Vite frontend. It supports account registration, income and expense transactions, monthly summaries, budgets, filters, and CSV export.

## Run locally

1. Install Python 3.10 or newer and create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

2. Set `SECRET_KEY` and `JWT_SECRET_KEY` in `.env` to long random secrets. To use the linked Supabase project, replace `YOUR_DATABASE_PASSWORD` in `SUPABASE_DB_URL` with the database password from Supabase **Project Settings → Database**. URL-encode special characters in the password. The connection uses TLS (`sslmode=require`). Leave `SUPABASE_DB_URL` unset to use local SQLite.

3. Start the API:

   ```powershell
   flask --app wsgi:app run --debug
   ```

   The app creates the SQLAlchemy tables when it starts. Existing local SQLite data is not copied to Supabase.

4. In another terminal, start the frontend:

   ```powershell
   cd frontend
   Copy-Item .env.example .env
   npm install
   npm run dev
   ```

   Open http://localhost:5173. Set `VITE_API_URL` if the API is not at `http://127.0.0.1:5000/api`.

## Deploy

The root `render.yaml` configures the Flask API on Render. Add `SUPABASE_DB_URL` in Render using the Supabase connection string and set `CORS_ORIGINS` to the deployed frontend origin(s). Import `frontend` as the Vercel root directory and set `VITE_API_URL` to the Render API URL ending in `/api`.

The backend connects to Supabase Postgres with its server-side database credential. Do not put the database password or a Supabase service-role key in the React app. The app's Flask/JWT authentication remains responsible for user accounts; SQLAlchemy owns data access and applies `user_id` ownership filters in the API.

## Testing

### Run the automated checks

From the repository root, install the backend requirements and run the API suite:

```powershell
py -m pip install -r requirements.txt
py -m unittest discover -s tests -v
```

The API tests use a fresh in-memory SQLite database for each test. They do not connect to Supabase or modify real accounts. The frontend has no separate test script; check its production build with:

```powershell
cd frontend
npm ci
npm run build
```

### Test fixtures

All fixture data is synthetic. Unit-test accounts are created in the isolated test database and disappear after each test. The load run also used a temporary local SQLite database that was removed afterwards.

| Fixture | Values used |
| --- | --- |
| Successful API registration/login | Name `Test User`; `login@example.com`; test-only password `correct-horse-123`. Login also checks uppercase `LOGIN@example.com` normalization. |
| Rejected login | `login@example.com` with test-only password `wrong`; expected HTTP 401. |
| Ownership test accounts | `alice@example.com` (`Test User`) and `bob@example.com` (`Other User`). |
| Transaction fixture | `Groceries`, amount `42.50`, expense, category `Food & drink`, date `2026-10-20`, note `weekly`. Dashboard expects October spending `42.50` and a budget of `500.00`; the fixture is then updated to `50.00` and deleted. |
| Validation cases | Registration name `X`, email `bad`, password `short`; invalid transaction amount `-1`; expected HTTP 400 responses. |
| CSV formula-safety case | Transaction title `=1+1`; exported cell must be prefixed as `'=1+1`. |
| CORS origin | `https://expense-tracker-two-omega-62.vercel.app`; the local preflight response must allow this origin. |
| Load-test account | Name `Load Test`, dynamically generated `@example.invalid` email, synthetic password `load-test-password-123`. Exists only in the temporary load database. |
| Load-test transaction dataset | 600 synthetic October 2026 expenses, each `12.50`, category `Food & drink`, spread across October 1–28. Expected monthly spending: `7500.00`. |

The fixture passwords above are test values only. Never reuse them for a real account.

### Recorded local results

Snapshot recorded on 2026-10-28 using Python 3.14, Vite 5.4.21, an in-process Flask test client, and local SQLite. Timings are environment-specific and are not Render or Supabase capacity figures.

| Check | Workload | Result |
| --- | --- | --- |
| API unit suite | 4 tests: auth, transaction/budget/dashboard, validation/CSV, CORS | 4 passed; 0 failed; about 1.2 seconds. |
| Frontend production build | Vite transforms and bundles the React app | Passed; 34 modules transformed. Output: 0.98 kB HTML, 20.44 kB CSS (5.19 kB gzip), 376.65 kB JS (124.42 kB gzip). |
| Local health burst | 500 requests, 10 concurrent clients | 500 succeeded; 0 errors; about 1,860 requests/second; p95 1.76 ms. |
| Dashboard reads | 200 authenticated requests, 10 concurrent clients, 600 seeded expenses | 200 succeeded; 0 errors; 19.7 requests/second; mean 504 ms; p95 554 ms. |
| Password login | 50 login requests, 10 concurrent clients | 50 succeeded; 0 errors; 38.1 requests/second; mean 254 ms; p95 277 ms. |
| Transaction writes | 50 authenticated creates, 10 concurrent clients | 50 succeeded; 0 errors; 121.2 requests/second; mean 46 ms; p95 253 ms. |

The dashboard, login, and write measurements use the local Flask app and a temporary SQLite database. They are useful for regression checks, but do not predict production performance with Render, network latency, or Supabase Postgres.

## Schema changes

Fresh databases get the `user`, `expense`, and `budget` tables from SQLAlchemy `create_all()`. For tracked schema changes, use Flask-Migrate:

```powershell
flask --app wsgi:app db init
flask --app wsgi:app db migrate -m "describe the change"
flask --app wsgi:app db upgrade
```

Commit the generated `migrations/` directory after initializing it once. For a production database with data, apply migrations before deploying code that depends on a schema change.

## Configuration

- `SUPABASE_DB_URL`: Supabase PostgreSQL connection URL; takes precedence over `DATABASE_URL`.
- `DATABASE_URL`: optional SQLAlchemy database URL (SQLite is used when neither URL is set).
- `SECRET_KEY`, `JWT_SECRET_KEY`: Flask session and API token signing secrets.
- `CORS_ORIGINS`: comma-separated allowed frontend origins.

Keep `.env` private; it is ignored by Git. The `/api/health` endpoint is the service health check.
