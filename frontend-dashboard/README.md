# Nutrition-Aware Recipe Recommendation System

## 1. Project Overview
Nutrition-Aware Recipe Recommendation System — capstone demo (PJK-GM053). Hybrid cascade: NCF Collaborative Filtering → TF-IDF Content-Based Filtering → Nutrition Scoring.

## 2. Prerequisites
- Python 3.13 with venv
- Node.js (for http-server)
- PostgreSQL running on port 5433
- Database: `nutrition_recipe_db` with tables `recipes` and `interactions`

## 3. Backend Setup
```bash
# From repo root
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
# Runs on http://localhost:8000
```

## 4. Frontend Setup
```bash
cd frontend-dashboard
npx http-server . -p 3000
# Open http://localhost:3000
```

## 5. Getting a Valid user_id
Only 19,123 users from the training dataset are supported. Get one from PostgreSQL:
```sql
SELECT user_id, COUNT(*) as interactions
FROM interactions
GROUP BY user_id
ORDER BY interactions DESC
LIMIT 10;
```

## 6. API Endpoints
- `POST /recommend` — hybrid recommendations
- `GET /stats` — dataset statistics
- `GET /recipe/{recipe_id}` — recipe detail
- `GET /user/{user_id}/history` — user interaction history

## 7. Model Files Required
```
cf/outputs/models/best_cf_model_ncf.pkl
cf/outputs/models/user2idx.pkl
cf/outputs/models/item2idx.pkl
cf/outputs/models/idx2item.pkl
cbf/outputs/models/best_cbf_model_tfidf.pkl
```

## 8. Environment Variables
Copy `backend/.env.example` to `.env` in repo root and fill in values.
