<<<<<<< HEAD
# Expense-Tracker
=======
# Pennywise — Personal Expense Tracker

A responsive expense tracker with a Flask JSON API and a separate React/Vite frontend. It uses SQLAlchemy, Flask-Login for the original server-rendered app, JWT bearer auth for the SPA, SQLite, Bootstrap styling, and Chart.js.

## Features

- Private accounts with Werkzeug password hashing and session-based authentication
- Create, edit, delete, and browse income and expense transactions
- Category, month, date-range, transaction-type, and amount/date sorting filters
- Monthly income, spending, balance, category breakdown, and six-month spending trend
- Per-month budget guide with progress indicator
- CSV export of transactions
- CSRF protection, server-side validation, account ownership checks, and responsive layouts
- JSON API for the React frontend with signed, expiring JWT access tokens

## Run locally

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies and set local configuration:

   ```powershell
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

4. Replace `SECRET_KEY` and `JWT_SECRET_KEY` in `.env` with long random secrets, then start the API:

   ```powershell
   flask --app wsgi:app run --debug
   ```

   SQLite data is stored under `instance/expense_tracker.db`.

5. In another terminal, start the React frontend:

   ```powershell
   cd frontend
   Copy-Item .env.example .env
   npm install
   npm run dev
   ```

   Open http://localhost:5173. Set `VITE_API_URL` to the API base (including `/api`) in `frontend/.env` if it differs from `http://127.0.0.1:5000/api`.

## Deploy to Render and Vercel

The repository needs to be pushed to a Git provider before either host can build it.

1. Create a Render web service from the repository using the root `render.yaml` blueprint. The service runs `gunicorn wsgi:app`; SQLite is stored on the configured persistent disk.
2. Copy the Render service URL, such as `https://your-service.onrender.com`.
3. Import the same repository in Vercel and set the project's **Root Directory** to `frontend`.
4. Set Vercel's build output to the Vite defaults (`npm run build`, `dist`) and add `VITE_API_URL=https://your-service.onrender.com/api` for Production, Preview, and Development as needed.
5. Set Render's `CORS_ORIGINS` to the Vercel production URL (and any preview URLs you use), comma-separated. The blueprint includes a Vercel subdomain pattern for preview builds.

The frontend and backend must use matching deployed URLs. The API's `/api/health` endpoint is the Render health check.

## Database migrations

The app creates tables automatically for a fresh database. For tracked schema changes, use Flask-Migrate:

```powershell
flask --app wsgi:app db init
flask --app wsgi:app db migrate -m "describe the change"
flask --app wsgi:app db upgrade
```

Commit the generated `migrations/` directory after initializing it once.

## Production

Set a strong `SECRET_KEY` and a persistent `DATABASE_URL` in the host environment. Use PostgreSQL for a multi-instance deployment; local SQLite files are not shared across ephemeral instances. Start with:

```sh
gunicorn wsgi:app
```

`render.yaml` includes a starter Render configuration and persistent disk for SQLite. Render generates separate Flask and JWT secrets automatically.

## Notes

- Bootstrap and fonts are loaded from public CDNs; Chart.js is included in the frontend bundle.
- The `.env` file is ignored by Git; keep credentials out of source control.
- Flask-Migrate is included for database evolution. The fresh install uses `create_all()` so it is immediately runnable before a migration history is initialized.
>>>>>>> origin/master
