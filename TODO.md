# TODO - FastAPI Nutrition-Aware Recipe Backend

- [ ] Create backend project skeleton (main.py, database.py, routers, pipeline, schemas)
- [ ] Implement model loading at startup (CF/CBF/Nutrition)
- [ ] Implement /recommend cascade (CF -> CBF -> Nutrition -> final ranking)
- [ ] Implement /stats, /recipe/{id}, /user/{id}/history
- [ ] Add CORS + asyncpg postgres access
- [ ] Add request/response Pydantic v2 schemas
- [ ] Ensure nutrition scoring uses `recipes.nutrition` numeric[] directly
- [ ] Run local smoke test (uvicorn start)

