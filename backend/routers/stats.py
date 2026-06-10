from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Request

from ..database import get_pool

router = APIRouter(prefix="", tags=["stats"])

@router.get("/stats")
async def stats(request: Request):

    app = request.app
    pool = await get_pool(app)

    total_recipes = await pool.fetchval("SELECT COUNT(*) FROM recipes")

    total_users = await pool.fetchval("SELECT COUNT(DISTINCT user_id) FROM interactions")
    total_interactions = await pool.fetchval("SELECT COUNT(*) FROM interactions")

    if total_users is None or total_recipes is None or total_users == 0 or total_recipes == 0:
        sparsity = 1.0
    else:
        denom = float(total_users) * float(total_recipes)
        sparsity = 1.0 - (float(total_interactions) / denom)

    return {
        "total_recipes": int(total_recipes or 0),
        "total_users": int(total_users or 0),
        "total_interactions": int(total_interactions or 0),
        "sparsity": float(sparsity),
    }

