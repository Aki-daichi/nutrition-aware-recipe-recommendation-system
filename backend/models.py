"""SQLAlchemy database models"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """Simple user account model."""
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)  # stable id used across app
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())



class Recipe(Base):
    """Recipe model"""
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    ingredients = Column(JSON, nullable=False)  # Array of ingredients
    
    # Nutritional information
    calories = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    carbs = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    fiber = Column(Float, nullable=True)
    sodium = Column(Float, nullable=True)
    
    # Additional info
    difficulty = Column(String(50), nullable=True)  # easy, medium, hard
    cooking_time = Column(Integer, nullable=True)  # in minutes
    servings = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserPreference(Base):
    """User dietary preferences model"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Dietary restrictions
    vegetarian = Column(Boolean, default=False)
    vegan = Column(Boolean, default=False)
    gluten_free = Column(Boolean, default=False)
    lactose_free = Column(Boolean, default=False)
    
    # Calorie preferences
    min_calories = Column(Float, nullable=True)
    max_calories = Column(Float, nullable=True)
    
    # Macro preferences
    min_protein = Column(Float, nullable=True)
    max_protein = Column(Float, nullable=True)
    min_carbs = Column(Float, nullable=True)
    max_carbs = Column(Float, nullable=True)
    min_fat = Column(Float, nullable=True)
    max_fat = Column(Float, nullable=True)
    
    allergies = Column(JSON, nullable=True)  # Array of allergies
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Recommendation(Base):
    """Recipe recommendations model"""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True, nullable=False)
    recipe_id = Column(Integer, nullable=False)
    recipe_name = Column(String(255), nullable=False)
    
    score = Column(Float, nullable=False)  # Recommendation score
    reasoning = Column(Text, nullable=True)  # Why this recipe was recommended
    
    is_rated = Column(Boolean, default=False)
    user_rating = Column(Float, nullable=True)  # 1-5 stars
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ModelEvaluation(Base):
    """Model evaluation metrics model"""
    __tablename__ = "model_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Evaluation metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    
    # Additional metrics
    total_recommendations = Column(Integer, default=0)
    total_ratings = Column(Integer, default=0)
    average_rating = Column(Float, nullable=True)
    
    evaluation_data = Column(JSON, nullable=True)  # Additional evaluation data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
