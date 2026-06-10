# Nutrition-Aware Recipe Recommendation System - FastAPI Backend

## Endpoints
- `POST /recommend`
- `GET /stats`
- `GET /recipe/{recipe_id}`
- `GET /user/{user_id}/history`

## Local dev
1. Create virtualenv and install dependencies (see root `requirements.txt`).
2. Create `.env` in project root:
   - `DATABASE_URL=postgresql://postgres:overlord123@localhost:5433/nutrition_recipe_db`
   - `MODEL_DIR=./models`
3. Run:
   - `uvicorn backend.main:app --reload`

## Notes
This backend expects PostgreSQL tables:
- `recipes`
- `interactions`

Model artifacts are loaded once on startup.

