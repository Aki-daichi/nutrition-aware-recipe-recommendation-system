# Frontend Dashboard

## 1. Overview

Demo UI for the Nutrition-Aware Recipe Recommendation System (PJK-GM053). It is a single-page app built with plain HTML, CSS, and JavaScript. No build step is required.

## 2. Prerequisites

- Backend API running on `http://localhost:8000`
- Node.js, optional and only needed for `http-server`

## 3. How to Run

Option A — with http-server, recommended to avoid CORS issues:

```bash
cd frontend-dashboard
npx http-server . -p 3000
# Open http://localhost:3000
```

Option B — open directly:

```text
Open frontend-dashboard/index.html in browser
API calls will use mock data if backend is unreachable
```

## 4. How to Start the Backend First

```bash
# From repo root
uvicorn backend.main:app --reload
# Runs on http://localhost:8000
```

## 5. How to Use the Dashboard

- Enter a valid `user_id` from the `interactions` table in PostgreSQL
- Adjust Top-N, from 5 to 20, and optional nutrition filters
- Click Submit
- Results show recipe cards with CF, CBF, Nutrition scores, and final ranking

## 6. Getting a Valid user_id

```sql
-- Run in PostgreSQL to find active users
SELECT user_id, COUNT(*) as interactions
FROM interactions
GROUP BY user_id
ORDER BY interactions DESC
LIMIT 10;
```

## 7. Mock Fallback

If the backend is unreachable, the UI automatically shows mock data so the demo still works without a running server.

## 8. API Endpoints Used

- `POST http://localhost:8000/recommend` — main recommendation call
- `GET http://localhost:8000/stats` — dataset statistics

## 9. Changing the API URL

Edit `app.js`, find `API_BASE_URL` at the top of the file and update it.
