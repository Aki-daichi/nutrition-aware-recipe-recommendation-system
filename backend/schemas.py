"""Pydantic schemas for request/response validation"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class RecipeBase(BaseModel):
    """Base recipe schema"""
    name: str
    description: Optional[str] = None
    ingredients: List[str]
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sodium: Optional[float] = None
    difficulty: Optional[str] = None
    cooking_time: Optional[int] = None
    servings: Optional[int] = None


class RecipeCreate(RecipeBase):
    """Recipe creation schema"""
    pass


class Recipe(RecipeBase):
    """Recipe response schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserPreferenceBase(BaseModel):
    """Base user preference schema"""
    vegetarian: bool = False
    vegan: bool = False
    gluten_free: bool = False
    lactose_free: bool = False
    min_calories: Optional[float] = None
    max_calories: Optional[float] = None
    min_protein: Optional[float] = None
    max_protein: Optional[float] = None
    min_carbs: Optional[float] = None
    max_carbs: Optional[float] = None
    min_fat: Optional[float] = None
    max_fat: Optional[float] = None
    allergies: Optional[List[str]] = None


class UserPreferenceCreate(UserPreferenceBase):
    """User preference creation schema"""
    user_id: str


class UserPreference(UserPreferenceBase):
    """User preference response schema"""
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecommendationBase(BaseModel):
    """Base recommendation schema"""
    recipe_id: int
    recipe_name: str
    score: float
    reasoning: Optional[str] = None


class RecommendationCreate(RecommendationBase):
    """Recommendation creation schema"""
    user_id: str


class RecommendationUpdate(BaseModel):
    """Recommendation update schema"""
    user_rating: Optional[float] = None


class Recommendation(RecommendationBase):
    """Recommendation response schema"""
    id: int
    user_id: str
    is_rated: bool
    user_rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelEvaluationBase(BaseModel):
    """Base model evaluation schema"""
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    total_recommendations: int = 0
    total_ratings: int = 0
    average_rating: Optional[float] = None
    evaluation_data: Optional[Dict[str, Any]] = None


class ModelEvaluation(ModelEvaluationBase):
    """Model evaluation response schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Request/Response schemas
class GetRecommendationsRequest(BaseModel):
    """Request schema for getting recommendations"""
    user_id: str
    num_recommendations: int = 5


class RecommendationResponse(BaseModel):
    """Response schema for recommendations"""
    recommendations: List[Recommendation]
    total_count: int
