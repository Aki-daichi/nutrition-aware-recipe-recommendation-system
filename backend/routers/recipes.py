from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, HTTPException

from ..database import get_pool

router = APIRouter(prefix="", tags=["recipes"])


@router.get("/recipe/{recipe_id}")
async def get_recipe(recipe_id: int, app):
    pool = await get_pool(app)
    row = await pool.fetchrow(
        """
        SELECT id, name, minutes, tags, ingredients, n_steps, description, nutrition
        FROM recipes
        WHERE id=$1
        """,
        recipe_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="recipe not found")

    r = dict(row)
    nutrition = r["nutrition"] or []

    # indexes from prompt
    return {
        "recipe_id": int(r["id"]),
        "name": r["name"],
        "minutes": r["minutes"],
        "tags": r["tags"] or [],
        "ingredients": r["ingredients"] or [],
        "n_steps": int(r["n_steps"]),
        "description": r["description"],
        "calories": float(nutrition[0]) if len(nutrition) > 0 and nutrition[0] is not None else 0.0,
        "nutrition": {
            "total_fat_pdv": float(nutrition[1]) if len(nutrition) > 1 and nutrition[1] is not None else 0.0,
            "sugar_pdv": float(nutrition[2]) if len(nutrition) > 2 and nutrition[2] is not None else 0.0,
            "sodium_pdv": float(nutrition[3]) if len(nutrition) > 3 and nutrition[3] is not None else 0.0,
            "protein_pdv": float(nutrition[4]) if len(nutrition) > 4 and nutrition[4] is not None else 0.0,
            "saturated_fat_pdv": float(nutrition[5]) if len(nutrition) > 5 and nutrition[5] is not None else 0.0,
            "carbohydrates_pdv": float(nutrition[6]) if len(nutrition) > 6 and nutrition[6] is not None else 0.0,
        },
    }


@router.get("/user/{user_id}/history")
async def user_history(user_id: int, app):
    pool = await get_pool(app)

    exists = await pool.fetchval(
        "SELECT 1 FROM interactions WHERE user_id=$1 LIMIT 1",
        user_id,
    )
    if not exists:
        raise HTTPException(status_code=404, detail="user not found")

    rows = await pool.fetch(
        """
        SELECT recipe_id, rating, date
        FROM interactions
        WHERE user_id=$1
        ORDER BY date DESC
        """,
        user_id,
    )

    recipe_ids = [int(r["recipe_id"]) for r in rows]

    recipes_rows = await pool.fetch(
        """
        SELECT id, name
        FROM recipes
        WHERE id = ANY($1::int[])
        """,
        recipe_ids,
    )
    name_map = {int(r["id"]): r["name"] for r in recipes_rows}

    recipes = []
    for r in rows:
        rid = int(r["recipe_id"])
        recipes.append(
            {
                "recipe_id": rid,
                "name": name_map.get(rid, ""),
                "rating": float(r["rating"]) if r["rating"] is not None else 0.0,
                "date": str(r["date"]),
            }
        )

    interaction_count = len(recipes)

    return {"user_id": user_id, "interaction_count": interaction_count, "recipes": recipes}

