"""Database seed script to populate initial data"""
from backend.database import SessionLocal
from backend.models import Recipe, ModelEvaluation
from datetime import datetime

def seed_recipes():
    """Add sample recipes to database"""
    db = SessionLocal()
    
    sample_recipes = [
        Recipe(
            name="Grilled Chicken Salad",
            description="Healthy grilled chicken with mixed greens and light vinaigrette",
            ingredients=["chicken breast", "mixed greens", "tomato", "cucumber", "olive oil", "vinegar"],
            calories=350,
            protein=35,
            carbs=15,
            fat=15,
            fiber=5,
            sodium=300,
            difficulty="easy",
            cooking_time=20,
            servings=2
        ),
        Recipe(
            name="Quinoa Buddha Bowl",
            description="Nutritious and colorful bowl with quinoa, vegetables, and tahini dressing",
            ingredients=["quinoa", "chickpeas", "sweet potato", "kale", "tahini", "lemon"],
            calories=420,
            protein=15,
            carbs=55,
            fat=14,
            fiber=8,
            sodium=250,
            difficulty="easy",
            cooking_time=25,
            servings=2
        ),
        Recipe(
            name="Baked Salmon with Asparagus",
            description="Omega-3 rich salmon baked with fresh asparagus",
            ingredients=["salmon fillet", "asparagus", "lemon", "garlic", "olive oil"],
            calories=380,
            protein=40,
            carbs=10,
            fat=20,
            fiber=2,
            sodium=180,
            difficulty="medium",
            cooking_time=25,
            servings=2
        ),
        Recipe(
            name="Vegetable Stir Fry",
            description="Quick and colorful vegetable stir fry with brown rice",
            ingredients=["broccoli", "bell pepper", "snap peas", "brown rice", "soy sauce", "ginger"],
            calories=320,
            protein=12,
            carbs=48,
            fat=8,
            fiber=6,
            sodium=400,
            difficulty="easy",
            cooking_time=20,
            servings=2
        ),
        Recipe(
            name="Smoothie Bowl",
            description="Creamy acai smoothie bowl topped with granola and fresh fruits",
            ingredients=["acai", "yogurt", "banana", "berries", "granola", "coconut"],
            calories=280,
            protein=10,
            carbs=42,
            fat=8,
            fiber=5,
            sodium=80,
            difficulty="easy",
            cooking_time=5,
            servings=1
        ),
        Recipe(
            name="Lentil Soup",
            description="Hearty and protein-rich lentil soup with vegetables",
            ingredients=["lentils", "onion", "carrot", "celery", "vegetable broth", "tomato"],
            calories=210,
            protein=18,
            carbs=32,
            fat=2,
            fiber=8,
            sodium=600,
            difficulty="easy",
            cooking_time=40,
            servings=4
        ),
        Recipe(
            name="Grilled Tofu Wrap",
            description="Plant-based wrap with grilled tofu and fresh vegetables",
            ingredients=["tofu", "wrap", "lettuce", "tomato", "cucumber", "hummus"],
            calories=290,
            protein=14,
            carbs=35,
            fat=10,
            fiber=5,
            sodium=350,
            difficulty="easy",
            cooking_time=15,
            servings=1
        ),
        Recipe(
            name="Turkey Meatballs",
            description="Lean protein meatballs with whole wheat pasta",
            ingredients=["ground turkey", "pasta", "tomato sauce", "garlic", "herbs"],
            calories=380,
            protein=32,
            carbs=42,
            fat=8,
            fiber=4,
            sodium=450,
            difficulty="medium",
            cooking_time=30,
            servings=3
        ),
    ]
    
    for recipe in sample_recipes:
        existing = db.query(Recipe).filter(Recipe.name == recipe.name).first()
        if not existing:
            db.add(recipe)
            print(f"✓ Added recipe: {recipe.name}")
    
    db.commit()
    db.close()


def seed_evaluation():
    """Add sample evaluation metrics"""
    db = SessionLocal()
    
    evaluation = ModelEvaluation(
        accuracy=0.85,
        precision=0.82,
        recall=0.78,
        f1_score=0.80,
        rmse=0.45,
        mae=0.32,
        total_recommendations=150,
        total_ratings=120,
        average_rating=4.2,
        evaluation_data={
            "model_version": "1.0",
            "training_date": "2024-01-15",
            "test_set_size": 50
        }
    )
    
    db.add(evaluation)
    db.commit()
    print("✓ Added evaluation metrics")
    db.close()


if __name__ == "__main__":
    print("Seeding database...")
    seed_recipes()
    seed_evaluation()
    print("\n✅ Database seeding completed!")
