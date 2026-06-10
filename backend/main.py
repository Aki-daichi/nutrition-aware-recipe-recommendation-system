from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncpg

from .routers.recommend import router as recommend_router
from .routers.stats import router as stats_router
from .routers.recipes import router as recipes_router

from .settings import get_settings
from .startup import startup_models

app = FastAPI(title="Nutrition-Aware Recipe Recommendation API")

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommend_router)
app.include_router(stats_router)
app.include_router(recipes_router)


@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(
        "postgresql://postgres:overlord123@localhost:5433/nutrition_recipe_db"
    )
    await startup_models(app)


@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()

