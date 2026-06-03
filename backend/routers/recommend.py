from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, HTTPException

from ..database import get_pool
from ..models.schemas import RecommendRequest, RecommendResponse

router = APIRouter(prefix="", tags=["recommend"])


async def _fetch_user_history(pool: asyncpg.Pool, user_id: int) -> list[dict[str, Any]]:
    rows = await pool.fetch(
        """
        SELECT recipe_id, rating, date
        FROM interactions
        WHERE user_id=$1 AND rating>0
        """,
        user_id,
    )
    return [dict(r) for r in rows]


async def _fetch_recipes_by_ids(pool: asyncpg.Pool, recipe_ids: list[int]) -> dict[int, dict[str, Any]]:
    if not recipe_ids:
        return {}

    # asyncpg has array support
    rows = await pool.fetch(
        """
        SELECT id, name, minutes, tags, ingredients, n_steps, description, nutrition, n_ingredients
        FROM recipes
        WHERE id = ANY($1::int[])
        """,
        recipe_ids,
    )
    out: dict[int, dict[str, Any]] = {}
    for r in rows:
        row = dict(r)
        out[int(row["id"])] = {
            "name": row["name"],
            "minutes": row["minutes"],
            "tags": row["tags"] or [],
            "ingredients": row["ingredients"] or [],
            "n_steps": row["n_steps"],
            "description": row["description"],
            "nutrition": row["nutrition"],
            "n_ingredients": row["n_ingredients"],
        }
    return out


from fastapi import Request


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest, request: Request):
    pool = await get_pool(request.app)

    # Stage 1: CF candidate generation

    cf_artifacts = request.app.state.cf


    try:
        cf_candidates = cf_artifacts and __import__("backend.pipeline.cf", fromlist=["score_candidates"]).score_candidates(
            cf_artifacts, req.user_id, top_k=req.top_n * 10
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="user_id not found in training data")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # User interaction history
    history = await _fetch_user_history(pool, req.user_id)
    past_recipe_ids = [int(h["recipe_id"]) for h in history]

    # Optional ref_recipe_id anchor (not fully implemented - uses history only per spec otherwise)
    if req.ref_recipe_id is not None:
        # Treat ref recipe as history seed
        past_recipe_ids = [int(req.ref_recipe_id)]

    candidate_recipe_ids = [c["recipe_id"] for c in cf_candidates]

    # Fetch candidate recipe rows incl nutrition numeric[]
    candidate_rows = await _fetch_recipes_by_ids(pool, candidate_recipe_ids)

    # Stage 2-4 hybrid
    from ..pipeline.hybrid import run_hybrid

    # Stage 2 uses past_recipe_ids for user profile
    results = run_hybrid(
        request.app.state.cf,
        request.app.state.cbf,
        request.app.state.nutrition,

        user_id=req.user_id,
        candidate_cf=cf_candidates,
        candidate_recipe_rows=candidate_rows,
        past_recipe_ids=past_recipe_ids,
        min_nutrition_score=req.min_nutrition_score,
        max_calories=req.max_calories,
    )

    # Top-N final
    return {"user_id": req.user_id, "recommendations": results[: req.top_n]}


