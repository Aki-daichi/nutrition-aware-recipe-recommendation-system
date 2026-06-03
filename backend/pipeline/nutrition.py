from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class NutritionArtifacts:
    # rule-based scorer could be stored here if needed
    scorer: Any


def load_nutrition() -> NutritionArtifacts:
    # Nutrition stage is rule-based scoring in this repo.
    # In the requested spec, we also use PostgreSQL numeric[] directly; we will compute a normalized nutrition_score from those values.
    from nutrition.scoring import NutritionScorer

    return NutritionArtifacts(scorer=NutritionScorer())


def extract_nutrition_values(nutrition_arr: list[float] | tuple[float, ...]) -> dict[str, float]:
    # Expected indexes: [0]=calories, [1]=total_fat_pdv, [2]=sugar_pdv, [3]=sodium_pdv,
    # [4]=protein_pdv, [5]=saturated_fat_pdv, [6]=carbohydrates_pdv
    return {
        "calories": float(nutrition_arr[0]),
        "total_fat_pdv": float(nutrition_arr[1]),
        "sugar_pdv": float(nutrition_arr[2]),
        "sodium_pdv": float(nutrition_arr[3]),
        "protein_pdv": float(nutrition_arr[4]),
        "saturated_fat_pdv": float(nutrition_arr[5]),
        "carbohydrates_pdv": float(nutrition_arr[6]),
    }


def nutrition_score_from_values(scorer: Any, values: dict[str, float]) -> float:
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "calories": values["calories"],
                "total_fat_pdv": values["total_fat_pdv"],
                "sugar_pdv": values["sugar_pdv"],
                "sodium_pdv": values["sodium_pdv"],
                "protein_pdv": values["protein_pdv"],
                "saturated_fat_pdv": values["saturated_fat_pdv"],
                "carbohydrates_pdv": values["carbohydrates_pdv"],
            }
        ]
    )
    scored = scorer.calculate_score(df)
    return float(scored.loc[0, "nutrition_score"])

