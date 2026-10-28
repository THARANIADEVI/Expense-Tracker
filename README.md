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
