from typing import Any, Literal

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    user_id: int
    top_n: int = Field(default=10, ge=5, le=20)
    min_nutrition_score: float | None = None
    max_calories: float | None = None
    ref_recipe_id: int | None = None


class NutritionRecipeOut(BaseModel):
    total_fat_pdv: float
    sugar_pdv: float
    sodium_pdv: float
    protein_pdv: float
    saturated_fat_pdv: float
    carbohydrates_pdv: float


class RecipeOut(BaseModel):
    recipe_id: int
    name: str
    minutes: int
    tags: list[str]
    ingredients: list[str]
    n_steps: int
    description: str
    calories: float
    nutrition: NutritionRecipeOut


class UserHistoryRecipeOut(BaseModel):
    recipe_id: int
    name: str
    rating: float
    date: str


class UserHistoryOut(BaseModel):
    user_id: int
    interaction_count: int
    recipes: list[UserHistoryRecipeOut]


class RecommendationOut(BaseModel):
    rank: int
    recipe_id: int
    name: str
    minutes: int
    tags: list[str]
    n_ingredients: int
    calories: float

    nutrition_score: float
    cf_score: float
    similarity_score: float
    final_score: float
    dominant_signal: Literal["CF", "CBF", "Nutrition"]


class RecommendResponse(BaseModel):
    user_id: int
    recommendations: list[RecommendationOut]


class StatsResponse(BaseModel):
    total_recipes: int
    total_users: int
    total_interactions: int
    sparsity: float

