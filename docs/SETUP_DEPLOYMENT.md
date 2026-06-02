# Setup and Deployment

This document describes how to run the application locally and via Docker, based on repository scripts and Docker configuration.

## Prerequisites

- Python 3.10+
- PostgreSQL (13+ recommended)
- Optional: Docker + Docker Compose

## Environment variables

The backend reads env vars using `python-dotenv` in `backend/config.py`.

Common variables:
- `DATABASE_URL`
  - Default: `postgresql://postgres:postgres@localhost:5432/nutrition_recipe_db`
- `DEBUG`
- `HOST`, `PORT`
- Model loading:
  - `MODEL_FILENAME` (default: `best_cf_model_ncf.pkl`)
  - `MODEL_PATH`
    - Default behavior: if set to an absolute path, it is treated as a filesystem location.
    - Otherwise it is treated as a directory under `PICKLE_PATH`.
  - `PICKLE_PATH` (default: `.`)
- CORS configuration is hard-coded in `backend/config.py` via `CORS_ORIGINS`.

## Local development (recommended for development)

1. Create and activate a Python environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Configure `.env`
   - Use `.env.example` as a starting point.
4. Initialize database tables:
   - `python -c "from backend.database import init_db; init_db()"`
5. Seed sample data:
   - `python seed_db.py`
6. Run server:
   - `python -m backend.main`

Access:
- Dashboard: `http://localhost:8000/dashboard`
- Swagger: `http://localhost:8000/docs`

## Docker deployment (Docker Compose)

1. Start services:
   - `docker-compose up -d`
2. Seed database inside the backend container:
   - `docker exec nutrition_recipe_api python seed_db.py`
3. Open:
   - `http://localhost:8000/dashboard`

Notes:
- `docker-compose.yml` maps PostgreSQL and sets `DATABASE_URL` for the backend container.
- `Dockerfile.backend` runs uvicorn against `backend.main:app`.

