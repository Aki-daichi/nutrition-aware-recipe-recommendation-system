from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class HybridArtifacts:
    cf: Any
    cbf: Any
    nutrition: Any


def _minmax_norm(values: list[float]) -> list[float]:
    if not values:
        return []
    v = np.asarray(values, dtype=np.float64)
    mn = float(np.min(v))
    mx = float(np.max(v))
    if mx - mn < 1e-12:
        return [0.0 for _ in values]
    return [float((x - mn) / (mx - mn)) for x in values]


def run_hybrid(
    cf_artifacts,
    cbf_artifacts,
    nutrition_artifacts,
    *,
    user_id: int,
    candidate_cf: list[dict[str, Any]],
    candidate_recipe_rows: dict[int, dict[str, Any]],
    past_recipe_ids: list[int],
    min_nutrition_score: float | None = None,
    max_calories: float | None = None,
) -> list[dict[str, Any]]:
    # Stage 2: CBF reranking
    candidate_ids = [x["recipe_id"] for x in candidate_cf]
    cbf_scored = cbf_artifacts and __import__("backend.pipeline.cbf", fromlist=["score_cbf"]).score_cbf(
        cbf_artifacts,
        candidate_ids,
        past_recipe_ids,
    )

    sim_map = {x["recipe_id"]: float(x["similarity_score"]) for x in cbf_scored}

    # Stage 3: Nutrition scoring
    # Candidate rows already include nutrition numeric[] from PostgreSQL
    results = []
    for c in candidate_cf:
        rid = int(c["recipe_id"])
        row = candidate_recipe_rows.get(rid)
        if not row:
            continue
        nutrition_arr = row["nutrition"]
        values = __import__("backend.pipeline.nutrition", fromlist=["extract_nutrition_values"]).extract_nutrition_values(nutrition_arr)
        nutrition_score = __import__("backend.pipeline.nutrition", fromlist=["nutrition_score_from_values"]).nutrition_score_from_values(
            nutrition_artifacts.scorer, values
        )

        out = {
            "recipe_id": rid,
            "name": row["name"],
            "minutes": row["minutes"],
            "tags": row["tags"],
            "n_ingredients": row["n_ingredients"],
            "calories": float(values["calories"]),
            "nutrition_score": float(nutrition_score),
            "cf_score": float(c["cf_score"]),
            "similarity_score": float(sim_map.get(rid, 0.0)),
        }
        # Filters
        if min_nutrition_score is not None and out["nutrition_score"] < float(min_nutrition_score):
            continue
        if max_calories is not None and out["calories"] > float(max_calories):
            continue
        results.append(out)

    if not results:
        return []

    # Stage 4: Final ranking (normalize across candidate set)
    cf_norm = _minmax_norm([r["cf_score"] for r in results])
    sim_norm = _minmax_norm([r["similarity_score"] for r in results])
    nut_norm = _minmax_norm([r["nutrition_score"] for r in results])

    for i, r in enumerate(results):
        final_score = (0.5 * cf_norm[i]) + (0.3 * sim_norm[i]) + (0.2 * nut_norm[i])
        contrib_cf = 0.5 * cf_norm[i]
        contrib_cbf = 0.3 * sim_norm[i]
        contrib_nut = 0.2 * nut_norm[i]

        dominant = "CF"
        if contrib_cbf >= contrib_cf and contrib_cbf >= contrib_nut:
            dominant = "CBF"
        elif contrib_nut >= contrib_cf and contrib_nut >= contrib_cbf:
            dominant = "Nutrition"

        r["final_score"] = float(final_score)
        r["dominant_signal"] = dominant

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results

