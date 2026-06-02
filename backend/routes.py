"""FastAPI recommendation system routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Header
from sqlalchemy.orm import Session
from .database import get_db
from . import models
from . import schemas
from typing import List, Optional

import uuid
import hashlib

from .config import MODEL_FILENAME, MODEL_PATH, PICKLE_PATH
from .pipeline import CFRecipeRecommendationPipeline


router = APIRouter(prefix="/api", tags=["recommendations"])



# ==================== Recipe Endpoints ====================
@router.get("/recipes", response_model=List[schemas.Recipe])
def get_recipes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all recipes with pagination"""
    recipes = db.query(models.Recipe).offset(skip).limit(limit).all()
    return recipes


@router.get("/recipes/{recipe_id}", response_model=schemas.Recipe)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Get a specific recipe by ID"""
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("/recipes", response_model=schemas.Recipe)
def create_recipe(recipe: schemas.RecipeCreate, db: Session = Depends(get_db)):
    """Create a new recipe"""
    existing_recipe = db.query(models.Recipe).filter(models.Recipe.name == recipe.name).first()
    if existing_recipe:
        raise HTTPException(status_code=400, detail="Recipe already exists")
    
    db_recipe = models.Recipe(**recipe.dict())
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


# ==================== Auth (simple account system) ====================


def _get_current_username(x_username: Optional[str]) -> str:
    if not x_username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Username header")
    return x_username


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@router.post("/register")
def register(request: schemas.UserRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == request.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    user_id = str(uuid.uuid4())
    user = models.User(id=user_id, username=request.username, password_hash=_hash_password(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return schemas.UserRegisterResponse(user_id=user.id, username=user.username)


@router.post("/login")
def login(request: schemas.UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.password_hash != _hash_password(request.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # No JWT/session: simple demo token = username
    return schemas.UserLoginResponse(username=user.username, user_id=user.id)


def _get_current_user(x_username: Optional[str], db: Session) -> models.User:
    username = _get_current_username(x_username)
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return user


# ==================== User Profile / Preferences ====================
@router.get("/me", response_model=schemas.UserProfile)
def get_me(
    x_username: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    user = _get_current_user(x_username, db)
    return schemas.UserProfile(id=user.id, username=user.username)


@router.get("/me/preferences", response_model=schemas.UserPreference)
def get_my_preferences(
    x_username: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    user = _get_current_user(x_username, db)
    preference = db.query(models.UserPreference).filter(models.UserPreference.user_id == user.id).first()
    if not preference:
        raise HTTPException(status_code=404, detail="User preferences not found")
    return preference


@router.post("/me/preferences", response_model=schemas.UserPreference)
def upsert_my_preferences(
    preference: schemas.UserPreferenceBase,
    x_username: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    user = _get_current_user(x_username, db)

    db_preference = db.query(models.UserPreference).filter(models.UserPreference.user_id == user.id).first()

    if db_preference:
        for key, value in preference.dict().items():
            setattr(db_preference, key, value)
    else:
        db_preference = models.UserPreference(user_id=user.id, **preference.dict())
        db.add(db_preference)

    db.commit()
    db.refresh(db_preference)
    return db_preference


# Backward-compatible (still supported): preferences by user_id
@router.get("/users/{user_id}/preferences", response_model=schemas.UserPreference)
def get_user_preferences(user_id: str, db: Session = Depends(get_db)):
    preference = db.query(models.UserPreference).filter(models.UserPreference.user_id == user_id).first()
    if not preference:
        raise HTTPException(status_code=404, detail="User preferences not found")
    return preference


@router.post("/users/{user_id}/preferences", response_model=schemas.UserPreference)
def create_or_update_user_preferences(
    user_id: str,
    preference: schemas.UserPreferenceBase,
    db: Session = Depends(get_db)
):
    db_preference = db.query(models.UserPreference).filter(models.UserPreference.user_id == user_id).first()

    if db_preference:
        for key, value in preference.dict().items():
            setattr(db_preference, key, value)
    else:
        db_preference = models.UserPreference(user_id=user_id, **preference.dict())
        db.add(db_preference)

    db.commit()
    db.refresh(db_preference)
    return db_preference


# ==================== Recommendations Endpoints ====================

@router.post("/recommendations", response_model=schemas.RecommendationResponse)
def get_recommendations(
    request: schemas.GetRecommendationsRequest,
    db: Session = Depends(get_db),
):

    """
    Get personalized recipe recommendations for a user
    
    This endpoint integrates the ML model to generate recommendations
    based on user preferences and past ratings.
    """
    # Get user preferences
    user_prefs = db.query(models.UserPreference).filter(
        models.UserPreference.user_id == request.user_id
    ).first()
    
    if not user_prefs:
        raise HTTPException(status_code=404, detail="User preferences not found")
    
    # Get all recipes
    all_recipes = db.query(models.Recipe).all()
    
    if not all_recipes:
        raise HTTPException(status_code=404, detail="No recipes available")
    
    pipeline = CFRecipeRecommendationPipeline(
        model_path=MODEL_PATH,
        model_filename=MODEL_FILENAME,
        pickle_path=PICKLE_PATH,
    )

    # The pipeline expects user_id to be present in the dict-like preferences.
    # SQLAlchemy model -> dict conversion.
    user_pref_dict = {
        **{k: getattr(user_prefs, k) for k in [
            "user_id",
            "min_calories",
            "max_calories",
            "min_protein",
            "max_protein",
            "min_carbs",
            "max_carbs",
            "min_fat",
            "max_fat",
            "vegetarian",
            "vegan",
            "gluten_free",
            "lactose_free",
        ]},
    }

    # Convert ORM recipes to dicts for the pipeline.
    recipe_dicts = []
    for r in all_recipes:
        recipe_dicts.append(
            {
                "id": r.id,
                "name": r.name,
                "calories": r.calories,
                "protein": r.protein,
                "carbs": r.carbs,
                "fat": r.fat,
                "fiber": r.fiber,
                "sodium": r.sodium,
                "ingredients": r.ingredients,
                "cooking_time": r.cooking_time,
            }
        )

    top = pipeline.get_top_recommendations(
        user_preferences=user_pref_dict,
        recipes=recipe_dicts,
        n_recommendations=request.num_recommendations,
    )

    # Persist recommendations so the rating endpoint works.
    recommendations = []
    for item in top:
        recipe = item["recipe"]
        rec = models.Recommendation(
            user_id=request.user_id,
            recipe_id=int(recipe["id"]),
            recipe_name=str(recipe["name"]),
            score=float(item["score"]),
            reasoning=item.get("reasoning"),
        )
        db.add(rec)
        recommendations.append(rec)

    db.commit()
    for rec in recommendations:
        db.refresh(rec)

    return schemas.RecommendationResponse(
        recommendations=[schemas.Recommendation.from_orm(r) for r in recommendations],
        total_count=len(recommendations),
    )



@router.post("/recommendations/{recommendation_id}/rate")
def rate_recommendation(
    recommendation_id: int,
    update: schemas.RecommendationUpdate,
    db: Session = Depends(get_db)
):
    """Rate a recommendation"""
    recommendation = db.query(models.Recommendation).filter(
        models.Recommendation.id == recommendation_id
    ).first()
    
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    recommendation.is_rated = True
    recommendation.user_rating = update.user_rating
    
    db.commit()
    db.refresh(recommendation)
    
    return {"message": "Rating recorded", "recommendation": schemas.Recommendation.from_orm(recommendation)}


# ==================== Model Evaluation Endpoints ====================
@router.get("/evaluation/metrics", response_model=schemas.ModelEvaluation)
def get_latest_evaluation(db: Session = Depends(get_db)):
    """Get latest model evaluation metrics"""
    evaluation = db.query(models.ModelEvaluation).order_by(
        models.ModelEvaluation.created_at.desc()
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="No evaluation data available")
    
    return evaluation


@router.post("/evaluation/metrics", response_model=schemas.ModelEvaluation)
def create_evaluation(
    evaluation: schemas.ModelEvaluationBase,
    db: Session = Depends(get_db)
):
    """Save model evaluation metrics"""
    db_evaluation = models.ModelEvaluation(**evaluation.dict())
    db.add(db_evaluation)
    db.commit()
    db.refresh(db_evaluation)
    return db_evaluation


@router.get("/evaluation/recommendations-by-user")
def get_recommendations_statistics(db: Session = Depends(get_db)):
    """Get recommendation statistics"""
    total_recommendations = db.query(models.Recommendation).count()
    total_rated = db.query(models.Recommendation).filter(
        models.Recommendation.is_rated == True
    ).count()
    
    # Get average rating
    from sqlalchemy import func
    avg_rating = db.query(func.avg(models.Recommendation.user_rating)).filter(
        models.Recommendation.user_rating != None
    ).scalar()
    
    unique_users = db.query(func.count(func.distinct(models.Recommendation.user_id))).scalar()
    
    return {
        "total_recommendations": total_recommendations,
        "total_rated": total_rated,
        "unique_users": unique_users,
        "average_rating": float(avg_rating) if avg_rating else 0.0,
        "rating_percentage": (total_rated / total_recommendations * 100) if total_recommendations > 0 else 0
    }


# ==================== Health Check Endpoint ====================
@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}
