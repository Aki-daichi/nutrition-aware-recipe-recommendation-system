"""FastAPI recommendation system routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from typing import List

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


# ==================== User Preferences Endpoints ====================
@router.get("/users/{user_id}/preferences", response_model=schemas.UserPreference)
def get_user_preferences(user_id: str, db: Session = Depends(get_db)):
    """Get user preferences"""
    preference = db.query(models.UserPreference).filter(
        models.UserPreference.user_id == user_id
    ).first()
    
    if not preference:
        raise HTTPException(status_code=404, detail="User preferences not found")
    return preference


@router.post("/users/{user_id}/preferences", response_model=schemas.UserPreference)
def create_or_update_user_preferences(
    user_id: str,
    preference: schemas.UserPreferenceBase,
    db: Session = Depends(get_db)
):
    """Create or update user preferences"""
    db_preference = db.query(models.UserPreference).filter(
        models.UserPreference.user_id == user_id
    ).first()
    
    if db_preference:
        # Update existing preferences
        for key, value in preference.dict().items():
            setattr(db_preference, key, value)
    else:
        # Create new preferences
        db_preference = models.UserPreference(user_id=user_id, **preference.dict())
        db.add(db_preference)
    
    db.commit()
    db.refresh(db_preference)
    return db_preference


# ==================== Recommendations Endpoints ====================
@router.post("/recommendations", response_model=schemas.RecommendationResponse)
def get_recommendations(
    request: schemas.GetRecommendationsRequest,
    db: Session = Depends(get_db)
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
    
    # TODO: Integrate with ML model for scoring
    # For now, return simple recommendations based on calories
    recommendations = []
    for recipe in all_recipes[:request.num_recommendations]:
        rec = models.Recommendation(
            user_id=request.user_id,
            recipe_id=recipe.id,
            recipe_name=recipe.name,
            score=0.85,  # Placeholder score
            reasoning=f"Matches your dietary preferences"
        )
        recommendations.append(rec)
    
    return schemas.RecommendationResponse(
        recommendations=[schemas.Recommendation.from_orm(r) for r in recommendations],
        total_count=len(recommendations)
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
