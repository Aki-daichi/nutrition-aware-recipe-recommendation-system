# Setup & Installation Guide

## Project Structure

```
.
├── backend/                    # FastAPI backend
│   ├── main.py                # Main application
│   ├── config.py              # Configuration settings
│   ├── database.py            # Database connection
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   └── routes.py              # API routes
├── frontend/                   # Web dashboard
│   ├── index.html             # Home page
│   ├── dashboard.html         # Dashboard page
│   └── static/
│       ├── styles.css         # Styles
│       └── dashboard.js       # JavaScript
├── models/                     # ML models directory
├── docker-compose.yml         # Docker compose configuration
├── Dockerfile.backend         # Backend Docker image
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # Project documentation
```

## Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Docker & Docker Compose (optional)
- pip or conda

## Installation

### Option 1: Local Development Setup

#### 1. Clone and Setup Repository

```bash
cd nutrition-aware-recipe-recommendation-system
```

#### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Setup PostgreSQL

**Windows (using PostgreSQL installer):**
1. Download and install PostgreSQL from https://www.postgresql.org/download/windows/
2. During installation, remember the postgres password
3. Create a database:

```bash
psql -U postgres
CREATE DATABASE nutrition_recipe_db;
\q
```

**macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
createdb nutrition_recipe_db
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb nutrition_recipe_db
```

#### 5. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your database credentials
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/nutrition_recipe_db
```

#### 6. Initialize Database

```bash
# Run from the project root
python -c "from backend.database import init_db; init_db()"
```

#### 7. Run FastAPI Server

```bash
# From project root
python backend/main.py

# Or using uvicorn directly
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

#### 8. Access Dashboard

Open your browser and navigate to:
- Home: http://localhost:8000/
- Dashboard: http://localhost:8000/dashboard
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Option 2: Docker Setup (Recommended)

#### 1. Build and Run with Docker Compose

```bash
docker-compose up -d
```

This will:
- Start PostgreSQL on port 5432
- Start FastAPI backend on port 8000
- Automatically initialize the database

#### 2. Verify Services

```bash
# Check running containers
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f postgres
```

#### 3. Stop Services

```bash
docker-compose down
```

To also remove data:
```bash
docker-compose down -v
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database Schema

### Tables

#### recipes
- `id` (Integer, PK)
- `name` (String)
- `description` (Text)
- `ingredients` (JSON)
- `calories`, `protein`, `carbs`, `fat`, `fiber`, `sodium` (Float)
- `difficulty`, `cooking_time`, `servings` (String/Integer)
- `created_at`, `updated_at` (DateTime)

#### user_preferences
- `id` (Integer, PK)
- `user_id` (String, Unique)
- `vegetarian`, `vegan`, `gluten_free`, `lactose_free` (Boolean)
- `min/max_calories`, `min/max_protein`, `min/max_carbs`, `min/max_fat` (Float)
- `allergies` (JSON)
- `created_at`, `updated_at` (DateTime)

#### recommendations
- `id` (Integer, PK)
- `user_id`, `recipe_id`, `recipe_name` (String/Integer)
- `score` (Float)
- `reasoning` (Text)
- `is_rated` (Boolean)
- `user_rating` (Float)
- `created_at`, `updated_at` (DateTime)

#### model_evaluations
- `id` (Integer, PK)
- `accuracy`, `precision`, `recall`, `f1_score`, `rmse`, `mae` (Float)
- `total_recommendations`, `total_ratings`, `average_rating` (Integer/Float)
- `evaluation_data` (JSON)
- `created_at`, `updated_at` (DateTime)

## API Endpoints

### Recipes
- `GET /api/recipes` - Get all recipes
- `GET /api/recipes/{recipe_id}` - Get specific recipe
- `POST /api/recipes` - Create new recipe

### User Preferences
- `GET /api/users/{user_id}/preferences` - Get user preferences
- `POST /api/users/{user_id}/preferences` - Set user preferences

### Recommendations
- `POST /api/recommendations` - Get recommendations for user
- `POST /api/recommendations/{recommendation_id}/rate` - Rate a recommendation

### Evaluation
- `GET /api/evaluation/metrics` - Get latest evaluation metrics
- `POST /api/evaluation/metrics` - Save evaluation metrics
- `GET /api/evaluation/recommendations-by-user` - Get recommendation statistics

### Health
- `GET /api/health` - Health check

## Sample Requests

### Create a Recipe

```bash
curl -X POST "http://localhost:8000/api/recipes" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Healthy Quinoa Bowl",
    "description": "Nutritious quinoa with vegetables",
    "ingredients": ["quinoa", "broccoli", "tomato", "olive oil"],
    "calories": 450,
    "protein": 15,
    "carbs": 65,
    "fat": 12,
    "fiber": 8,
    "sodium": 200,
    "difficulty": "easy",
    "cooking_time": 25,
    "servings": 2
  }'
```

### Set User Preferences

```bash
curl -X POST "http://localhost:8000/api/users/user123/preferences" \
  -H "Content-Type: application/json" \
  -d '{
    "vegetarian": true,
    "vegan": false,
    "gluten_free": false,
    "lactose_free": false,
    "min_calories": 200,
    "max_calories": 600,
    "min_protein": 15,
    "max_carbs": 80,
    "allergies": ["peanuts"]
  }'
```

### Get Recommendations

```bash
curl -X POST "http://localhost:8000/api/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "num_recommendations": 5
  }'
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black backend/
```

### Linting

```bash
flake8 backend/
```

## Troubleshooting

### PostgreSQL Connection Error

If you get connection errors:

```bash
# Check if PostgreSQL is running
# Windows: Services > Check PostgreSQL service
# macOS: brew services list | grep postgresql
# Linux: sudo service postgresql status

# Verify connection string in .env
psql postgresql://postgres:password@localhost:5432/nutrition_recipe_db
```

### Port Already in Use

```bash
# Windows - Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

### Database Doesn't Exist

```bash
# Create database manually
psql -U postgres -c "CREATE DATABASE nutrition_recipe_db;"
```

## Integration with ML Model

To integrate your trained ML model:

1. Place model file in `models/` directory
2. Update `backend/routes.py` - `get_recommendations()` function
3. Load model and use for scoring recommendations
4. Update evaluation metrics endpoint with model performance

Example:

```python
# In backend/routes.py
import pickle

with open('models/recommendation_model.pkl', 'rb') as f:
    model = pickle.load(f)

# In get_recommendations endpoint
scores = model.predict(user_features)
```

## Project Status

- ✅ Backend API with FastAPI
- ✅ PostgreSQL database integration
- ✅ Web dashboard frontend
- ✅ Docker setup
- ⏳ ML model integration (in progress)
- ⏳ Advanced recommendation algorithm
- ⏳ User authentication
- ⏳ Advanced analytics

## Contact & Support

For questions or issues, please refer to the project documentation or create an issue in the repository.
