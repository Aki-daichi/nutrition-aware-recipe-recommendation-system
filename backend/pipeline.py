"""API Integration and Model Pipeline Demo

This module demonstrates how to integrate the trained ML model
with the FastAPI backend for generating recommendations.
"""

import pickle
import numpy as np
from typing import List, Dict


class RecipeRecommendationPipeline:
    """Pipeline for recipe recommendation with model integration"""

    def __init__(self, model_path: str = None):
        """
        Initialize the recommendation pipeline.
        
        Args:
            model_path: Path to trained model pickle file
        """
        self.model = None
        self.model_path = model_path
        
        if model_path:
            self.load_model(model_path)

    def load_model(self, model_path: str):
        """Load trained model from pickle file"""
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            print(f"✓ Model loaded from {model_path}")
        except Exception as e:
            print(f"✗ Error loading model: {e}")

    def prepare_user_features(self, user_preferences: Dict) -> np.ndarray:
        """
        Prepare user preference features for model input.
        
        Args:
            user_preferences: User preference dictionary
            
        Returns:
            Feature vector for model
        """
        features = [
            user_preferences.get('min_calories', 0),
            user_preferences.get('max_calories', 3000),
            user_preferences.get('min_protein', 0),
            user_preferences.get('max_protein', 150),
            user_preferences.get('min_carbs', 0),
            user_preferences.get('max_carbs', 300),
            user_preferences.get('min_fat', 0),
            user_preferences.get('max_fat', 100),
            int(user_preferences.get('vegetarian', False)),
            int(user_preferences.get('vegan', False)),
            int(user_preferences.get('gluten_free', False)),
            int(user_preferences.get('lactose_free', False)),
        ]
        return np.array(features).reshape(1, -1)

    def prepare_recipe_features(self, recipe: Dict) -> np.ndarray:
        """
        Prepare recipe features for model input.
        
        Args:
            recipe: Recipe dictionary
            
        Returns:
            Feature vector for model
        """
        features = [
            recipe.get('calories', 0),
            recipe.get('protein', 0),
            recipe.get('carbs', 0),
            recipe.get('fat', 0),
            recipe.get('fiber', 0),
            recipe.get('sodium', 0),
            len(recipe.get('ingredients', [])),
            recipe.get('cooking_time', 0) / 60,  # Normalize to hours
        ]
        return np.array(features).reshape(1, -1)

    def score_recipe(self, user_preferences: Dict, recipe: Dict) -> float:
        """
        Score a recipe for a user.
        
        Args:
            user_preferences: User preference dictionary
            recipe: Recipe dictionary
            
        Returns:
            Score between 0 and 1
        """
        if self.model is None:
            # Default scoring if model not loaded
            return self._default_score(user_preferences, recipe)
        
        try:
            user_features = self.prepare_user_features(user_preferences)
            recipe_features = self.prepare_recipe_features(recipe)
            
            # Combine features
            combined_features = np.hstack([user_features, recipe_features])
            
            # Get prediction from model
            score = self.model.predict(combined_features)[0]
            
            # Ensure score is between 0 and 1
            score = max(0, min(1, score))
            return float(score)
        except Exception as e:
            print(f"Error scoring recipe: {e}")
            return self._default_score(user_preferences, recipe)

    def _default_score(self, user_preferences: Dict, recipe: Dict) -> float:
        """
        Default scoring function based on nutritional preferences.
        
        Args:
            user_preferences: User preference dictionary
            recipe: Recipe dictionary
            
        Returns:
            Score between 0 and 1
        """
        score = 1.0
        
        # Check calorie range
        cal = recipe.get('calories', 0)
        min_cal = user_preferences.get('min_calories', 0)
        max_cal = user_preferences.get('max_calories', 3000)
        
        if not (min_cal <= cal <= max_cal):
            score -= 0.2
        
        # Check dietary restrictions
        if user_preferences.get('vegetarian') and 'meat' in recipe.get('name', '').lower():
            score -= 0.3
        
        if user_preferences.get('gluten_free') and 'wheat' in str(recipe.get('ingredients', [])).lower():
            score -= 0.2
        
        # Add some randomness for demo
        score += np.random.uniform(-0.05, 0.05)
        
        return max(0, min(1, score))

    def get_top_recommendations(
        self,
        user_preferences: Dict,
        recipes: List[Dict],
        n_recommendations: int = 5
    ) -> List[Dict]:
        """
        Get top N recipe recommendations for a user.
        
        Args:
            user_preferences: User preference dictionary
            recipes: List of recipe dictionaries
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of top recommendations with scores
        """
        recommendations = []
        
        for recipe in recipes:
            score = self.score_recipe(user_preferences, recipe)
            recommendations.append({
                'recipe': recipe,
                'score': score,
                'reasoning': self._generate_reasoning(user_preferences, recipe)
            })
        
        # Sort by score (descending) and return top N
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:n_recommendations]

    def _generate_reasoning(self, user_preferences: Dict, recipe: Dict) -> str:
        """Generate reasoning for recommendation"""
        reasons = []
        
        cal = recipe.get('calories', 0)
        min_cal = user_preferences.get('min_calories', 0)
        max_cal = user_preferences.get('max_calories', 3000)
        
        if min_cal <= cal <= max_cal:
            reasons.append("Matches your calorie goals")
        
        if recipe.get('protein', 0) >= user_preferences.get('min_protein', 0):
            reasons.append("Good protein content")
        
        if user_preferences.get('vegetarian') and 'meat' not in recipe.get('name', '').lower():
            reasons.append("Fits your vegetarian preferences")
        
        if reasons:
            return " | ".join(reasons)
        return "Matches your dietary preferences"


# Demo function to test the pipeline
def demo_pipeline():
    """Demonstration of the recommendation pipeline"""
    
    print("=" * 60)
    print("Recipe Recommendation Pipeline Demo")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = RecipeRecommendationPipeline()
    
    # Sample user preferences
    user_prefs = {
        'min_calories': 200,
        'max_calories': 600,
        'min_protein': 15,
        'max_protein': 50,
        'min_carbs': 20,
        'max_carbs': 80,
        'min_fat': 5,
        'max_fat': 25,
        'vegetarian': False,
        'vegan': False,
        'gluten_free': False,
        'lactose_free': False,
    }
    
    # Sample recipes
    recipes = [
        {
            'id': 1,
            'name': 'Grilled Chicken Salad',
            'calories': 350,
            'protein': 35,
            'carbs': 15,
            'fat': 15,
            'fiber': 5,
            'sodium': 300,
            'ingredients': ['chicken', 'lettuce', 'tomato'],
            'cooking_time': 20
        },
        {
            'id': 2,
            'name': 'Quinoa Buddha Bowl',
            'calories': 420,
            'protein': 15,
            'carbs': 55,
            'fat': 14,
            'fiber': 8,
            'sodium': 250,
            'ingredients': ['quinoa', 'vegetables'],
            'cooking_time': 25
        },
        {
            'id': 3,
            'name': 'Salmon with Asparagus',
            'calories': 380,
            'protein': 40,
            'carbs': 10,
            'fat': 20,
            'fiber': 2,
            'sodium': 180,
            'ingredients': ['salmon', 'asparagus'],
            'cooking_time': 25
        },
    ]
    
    print("\nUser Preferences:")
    print(f"  Calorie Range: {user_prefs['min_calories']}-{user_prefs['max_calories']} kcal")
    print(f"  Vegetarian: {user_prefs['vegetarian']}")
    
    print("\n" + "-" * 60)
    print("Generating Recommendations...")
    print("-" * 60)
    
    # Get recommendations
    recommendations = pipeline.get_top_recommendations(user_prefs, recipes, n_recommendations=3)
    
    # Display results
    for i, rec in enumerate(recommendations, 1):
        recipe = rec['recipe']
        score = rec['score']
        reasoning = rec['reasoning']
        
        print(f"\n{i}. {recipe['name']}")
        print(f"   Score: {score:.2%}")
        print(f"   Calories: {recipe['calories']} | Protein: {recipe['protein']}g")
        print(f"   Reason: {reasoning}")
    
    print("\n" + "=" * 60)
    print("✓ Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    demo_pipeline()
