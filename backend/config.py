"""Configuration settings for FastAPI application"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/nutrition_recipe_db"
)

# API Configuration
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
API_TITLE = "Nutrition-Aware Recipe Recommendation System"
API_DESCRIPTION = "Backend API untuk sistem rekomendasi resep berbasis nutrisi"
API_VERSION = "1.0.0"

# Model Configuration
MODEL_PATH = os.getenv("MODEL_PATH", "../models/")
PICKLE_PATH = os.getenv("PICKLE_PATH", "../")

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:5173",
]

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
