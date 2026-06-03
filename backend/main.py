from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.recommend import router as recommend_router
from .routers.stats import router as stats_router
from .routers.recipes import router as recipes_router

from .settings import get_settings
from .startup import startup_models

app = FastAPI(title="Nutrition-Aware Recipe Recommendation API")

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommend_router)
app.include_router(stats_router)
app.include_router(recipes_router)


@app.on_event("startup")
async def on_startup():
    await startup_models(app)

