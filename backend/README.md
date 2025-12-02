# Backend (FastAPI) - Starter

This folder contains a starter FastAPI backend for the Neusearch AI assignment.

Quick start (local):

1. Create a Python venv and install dependencies:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2. Ensure a Postgres instance is running and `DATABASE_URL` is set in env.
3. Run the app:

```powershell
uvicorn app.main:app --reload
```

Files of interest:
- `app/main.py` - FastAPI app and startup
- `app/api.py` - endpoints (`/api/scrape`, `/api/products`)
- `app/models.py` - SQLAlchemy models (products + product_chunks)
- `app/scraper/scraper.py` - scraper scaffold (replace with real scraping)
- `alembic/` - alembic config and env.py for migrations
