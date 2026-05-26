# 🚀 Quick Start Guide

## 5-Minute Setup

### For Windows Users

1. **Open PowerShell/Command Prompt** in project folder
2. **Run setup script**:
   ```bash
   .\setup.bat
   ```
3. **Edit .env file** with your database credentials
4. **Run server**:
   ```bash
   python backend/main.py
   ```
5. **Open browser**: http://localhost:8000/dashboard

### For Mac/Linux Users

1. **Open Terminal** in project folder
2. **Run setup script**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
3. **Edit .env file** with your database credentials
4. **Run server**:
   ```bash
   python backend/main.py
   ```
5. **Open browser**: http://localhost:8000/dashboard

### Using Docker (Recommended for Deployment)

1. **Start services**:
   ```bash
   docker-compose up -d
   ```
2. **Seed database**:
   ```bash
   docker exec nutrition_recipe_api python seed_db.py
   ```
3. **Open browser**: http://localhost:8000/dashboard

---

## What's Included?

### ✅ Backend API (FastAPI)
- 20+ REST endpoints
- Database models for recipes, users, recommendations, evaluations
- Pydantic validation schemas
- CORS middleware setup
- Health check endpoints

### ✅ Frontend Dashboard
- **Home Page**: Project overview and features
- **Dashboard**: Statistics and performance charts
- **Recommendations**: Get personalized recipe suggestions
- **Evaluation**: View model performance metrics
- **Recipes**: Browse recipe database

### ✅ Database (PostgreSQL)
- Recipes table with nutritional data
- User preferences table
- Recommendations table with ratings
- Model evaluations table

### ✅ ML Pipeline Integration
- `backend/pipeline.py`: Recommendation scoring engine
- Support for custom model integration
- Default scoring algorithm included
- Demo function for testing

### ✅ Docker Setup
- `docker-compose.yml`: One-command deployment
- `Dockerfile.backend`: Backend containerization
- PostgreSQL container setup

---

## Key Directories

```
backend/                    # FastAPI application
├── main.py               # Start here!
├── routes.py            # API endpoints
├── models.py            # Database models
├── database.py          # DB connection
└── pipeline.py          # ML integration

frontend/                  # Web dashboard
├── index.html           # Home page
├── dashboard.html       # Main dashboard
└── static/
    ├── styles.css
    └── dashboard.js

models/                    # Place ML models here
```

---

## API Examples

### Get All Recipes
```bash
curl http://localhost:8000/api/recipes
```

### Create a Recipe
```bash
curl -X POST http://localhost:8000/api/recipes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Recipe",
    "calories": 500,
    "protein": 25,
    "carbs": 60,
    "fat": 15,
    "ingredients": ["rice", "chicken"]
  }'
```

### Get Recommendations
```bash
curl -X POST http://localhost:8000/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "num_recommendations": 5
  }'
```

### Set User Preferences
```bash
curl -X POST http://localhost:8000/api/users/user123/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "vegetarian": true,
    "min_calories": 200,
    "max_calories": 600
  }'
```

---

## Important URLs

- **Home**: http://localhost:8000/
- **Dashboard**: http://localhost:8000/dashboard
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **API Base URL**: http://localhost:8000/api

---

## Database Credentials (Default)

```
Host: localhost
Port: 5432
Database: nutrition_recipe_db
User: postgres
Password: postgres
```

> ⚠️ Change these in `.env` file for production!

---

## Troubleshooting

### Port 8000 Already in Use
```bash
# Find and kill process
netstat -ano | findstr :8000    # Windows
lsof -ti:8000 | xargs kill -9   # Mac/Linux
```

### PostgreSQL Connection Failed
1. Check `.env` file DATABASE_URL
2. Verify PostgreSQL is running
3. Create database if missing: `createdb nutrition_recipe_db`

### ModuleNotFoundError
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Permission Denied (setup.sh)
```bash
chmod +x setup.sh
./setup.sh
```

---

## Development Commands

```bash
# Activate virtual environment
source venv/bin/activate          # Mac/Linux
venv\Scripts\activate.bat         # Windows

# Install dependencies
pip install -r requirements.txt

# Format code
black backend/

# Lint code
flake8 backend/

# Run tests
pytest

# Seed database
python seed_db.py

# Run API server
python backend/main.py

# Run demo pipeline
python -c "from backend.pipeline import demo_pipeline; demo_pipeline()"
```

---

## Next Steps

1. ✅ **Setup Complete** - Server is running
2. 📊 **Explore Dashboard** - Visit http://localhost:8000/dashboard
3. 🔄 **Integrate ML Model** - Place trained model in `models/` folder
4. 🧪 **Test API Endpoints** - Use Swagger UI at `/docs`
5. 📝 **Review Documentation** - Check README.md and SETUP.md

---

## Project Status

| Component | Status |
|-----------|--------|
| Backend API | ✅ Ready |
| Frontend Dashboard | ✅ Ready |
| Database | ✅ Ready |
| Docker Setup | ✅ Ready |
| ML Integration | ⏳ In Progress |
| Authentication | 🔲 Planned |

---

## Need Help?

- 📖 See [README.md](README.md) for full documentation
- 🔧 See [SETUP.md](SETUP.md) for detailed setup instructions
- 🐍 Check `backend/pipeline.py` for model integration examples
- 📊 Visit Swagger UI at http://localhost:8000/docs

---

**Last Updated**: May 26, 2026
**Version**: 1.0.0
