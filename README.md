# 🍽️ Nutrition-Aware Recipe Recommendation System

A comprehensive web-based system for personalized recipe recommendations based on nutritional preferences and dietary restrictions. Built with FastAPI, PostgreSQL, and modern web technologies.

## 📋 Project Overview

This capstone project implements an intelligent recipe recommendation system that:
- Provides AI-powered personalized recipe suggestions
- Tracks comprehensive nutritional information
- Allows users to set dietary preferences and restrictions
- Rates recommendations to improve the model
- Visualizes model performance metrics
- Exposes RESTful API for integration

## 🎯 Features

- **🎯 Smart Recommendations**: AI-powered suggestions based on nutritional goals
- **📊 Nutrition Tracking**: Detailed nutritional data for each recipe
- **🔍 Personalization**: Set dietary restrictions, allergies, and preferences
- **⭐ Rating System**: Provide feedback to improve recommendations
- **📈 Analytics Dashboard**: View model performance and statistics
- **🔗 RESTful API**: Easy integration with other applications
- **🐳 Docker Support**: Easy deployment with Docker Compose
- **💾 PostgreSQL Database**: Robust data management

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database
- **Pydantic** - Data validation

### Frontend
- **HTML5** - Markup
- **CSS3** - Styling
- **JavaScript (Vanilla)** - Interactivity
- **Chart.js** - Data visualization

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

## 📁 Project Structure

```
nutrition-aware-recipe-recommendation-system/
├── backend/                          # FastAPI backend
│   ├── main.py                      # Application entry point
│   ├── config.py                    # Configuration settings
│   ├── database.py                  # Database connection & setup
│   ├── models.py                    # SQLAlchemy ORM models
│   ├── schemas.py                   # Pydantic validation schemas
│   └── routes.py                    # API endpoints
├── frontend/                         # Web dashboard
│   ├── index.html                   # Home page
│   ├── dashboard.html               # Main dashboard
│   └── static/
│       ├── styles.css               # Styling
│       └── dashboard.js             # Frontend logic
├── models/                           # ML models directory
├── EDA-Recipe.ipynb                 # Recipe exploratory analysis
├── EDA-Interaction.ipynb            # User interaction analysis
├── parse_picke.ipynb                # Pickle file parsing
├── docker-compose.yml               # Docker orchestration
├── Dockerfile.backend               # Backend Docker image
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── seed_db.py                       # Database initialization script
├── SETUP.md                         # Detailed setup guide
└── README.md                        # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 13+
- Docker & Docker Compose (optional)

### Option 1: Docker (Recommended)

```bash
# Clone repository
cd nutrition-aware-recipe-recommendation-system

# Start services
docker-compose up -d

# Initialize database with sample data
docker exec nutrition_recipe_api python seed_db.py

# Access the application
# Dashboard: http://localhost:8000/dashboard
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python -c "from backend.database import init_db; init_db()"

# Seed sample data
python seed_db.py

# Run server
python backend/main.py
```

## 📚 API Endpoints

### Recipes
```
GET    /api/recipes                      - List all recipes
GET    /api/recipes/{id}                 - Get specific recipe
POST   /api/recipes                      - Create new recipe
```

### User Preferences
```
GET    /api/users/{user_id}/preferences  - Get user preferences
POST   /api/users/{user_id}/preferences  - Set user preferences
```

### Recommendations
```
POST   /api/recommendations              - Get recommendations
POST   /api/recommendations/{id}/rate    - Rate recommendation
```

### Evaluation
```
GET    /api/evaluation/metrics           - Get latest metrics
POST   /api/evaluation/metrics           - Save metrics
GET    /api/evaluation/recommendations-by-user  - Get statistics
```

## 🗄️ Database Schema

### Recipes Table
- Recipe information with complete nutritional data
- Difficulty level, cooking time, servings
- Ingredients list (JSON)

### User Preferences Table
- Dietary restrictions (vegetarian, vegan, gluten-free, lactose-free)
- Nutritional goals (calorie range, macros)
- Allergies list

### Recommendations Table
- Recommendation scores and reasoning
- User ratings and feedback
- Timestamp tracking

### Model Evaluations Table
- Performance metrics (accuracy, precision, recall, F1-score)
- Error metrics (RMSE, MAE)
- Statistical data

## 💻 Dashboard Features

### Home/Dashboard Page
- Real-time statistics cards
- Rating distribution chart
- Model performance visualization
- Key metrics overview

### Recommendations Page
- User preference setup
- Get personalized recommendations
- Rate recommendations
- View recommendation scores

### Model Evaluation Page
- Performance metrics display
- Metrics timeline chart
- Historical performance data
- Model statistics

### Recipes Page
- Browse recipe database
- View nutritional information
- Search and filter recipes

## 🔧 Configuration

Edit `.env` file:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/nutrition_recipe_db

# API
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Paths
MODEL_PATH=./models/
PICKLE_PATH=./
```

## 📊 Sample Data

Run the seed script to populate sample recipes and evaluation metrics:

```bash
python seed_db.py
```

This adds:
- 8 sample recipes with complete nutritional data
- Sample evaluation metrics for the model

## 🧪 Testing

### Automated Tests
```bash
pytest tests/
```

### Manual API Testing
```bash
# Using curl
curl http://localhost:8000/api/recipes

# Using Python requests
python -c "import requests; print(requests.get('http://localhost:8000/api/recipes').json())"
```

## 📖 Documentation

- **Full Setup Guide**: See [SETUP.md](SETUP.md)
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc

## 🔄 Integration with ML Model

To integrate your trained recommendation model:

1. Place trained model in `models/` directory
2. Update the `get_recommendations()` function in `backend/routes.py`
3. Load and use model for scoring:

```python
import pickle

with open('models/your_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Use model for predictions
scores = model.predict(user_features)
```

4. Update evaluation metrics endpoint with actual model performance

## 📈 Development Roadmap

- ✅ Backend API with FastAPI
- ✅ PostgreSQL integration
- ✅ Web dashboard
- ✅ Docker setup
- ⏳ ML model integration
- ⏳ Advanced recommendation algorithm
- ⏳ User authentication & authorization
- ⏳ Recommendation explanations
- ⏳ Advanced analytics
- ⏳ Performance optimization

## 🐛 Troubleshooting

### Connection Issues
```bash
# Verify PostgreSQL is running
psql postgresql://postgres:password@localhost:5432/nutrition_recipe_db

# Check API server
curl http://localhost:8000/api/health
```

### Port Conflicts
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Database Reset
```bash
# Drop and recreate database
python -c "from backend.database import Base, engine; Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)"
python seed_db.py
```

## 📝 Notes

- The project uses JSON columns for flexible storage (ingredients, allergies, evaluation data)
- All timestamps are stored in UTC
- Recommendation scores range from 0 to 1 (0-100%)
- User ratings are on a 1-5 star scale

## 👥 Team

Capstone Project - Nutrition-Aware Recipe Recommendation System
- POLBAN (Institut Pertanian Bogor)
- PIJAK Program

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## ✉️ Contact

For questions or support, please create an issue in the repository.

---

**Last Updated**: May 26, 2026
**Status**: Active Development
