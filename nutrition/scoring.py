import pandas as pd
import numpy as np

class NutritionScorer:
    def __init__(self, thresholds=None, rewards=None):
        """
        Initialize the nutrition scorer.
        Penalties (thresholds): points deducted for exceeding healthy limits.
        Rewards: points added (or penalties reduced) for healthy nutrients.
        """
        # Default user guidelines that can be overridden
        self.thresholds = thresholds or {
            'calories': 30.0,
            'total_fat_pdv': 30.0,
            'sugar_pdv': 20.0,
            'sodium_pdv': 20.0,
            'saturated_fat_pdv': 20.0
        }
        self.rewards = rewards or {
            'protein_pdv': 5.0,  # Setiap kelipatan 5% PDV protein mengurangi penalti / menambah bonus
            'fiber_pdv': 5.0     # Jika ke depannya diekstrak data serat (dietary fiber)
        }
        
    def calculate_score(self, df: pd.DataFrame, weight_col=None) -> pd.DataFrame:
        """
        Calculate a health score (0-100) based on nutritional values.
        Higher score = Healthier
        If weight_col is provided, values are normalized to per 100g equivalent before scoring.
        """
        df = df.copy()
        penalties = np.zeros(len(df))
        bonus = np.zeros(len(df))
        
        # Normalisasi ke basis per 100 gram jika weight_col (berat sajian dalam gram) diset
        multiplier = 1.0
        if weight_col and weight_col in df.columns:
            # Hindari division by zero
            weight_safe = df[weight_col].replace(0, 1)
            multiplier = 100.0 / weight_safe
        
        # We add penalties for exceeding healthy thresholds
        for nutrient, thr in self.thresholds.items():
            if nutrient in df.columns:
                # Apply normalization factor
                val = df[nutrient] * multiplier
                excess = np.maximum(0, val - thr)
                # Normalize penalty (e.g., every 10% over threshold drops 5 points)
                penalties += (excess / 10.0) * 5.0
                
        # We add bonuses for healthy nutrients (Protein, Fiber)
        for nutrient, base_val in self.rewards.items():
            if nutrient in df.columns:
                val = df[nutrient] * multiplier
                # Setiap kelipatan base_val menambah bonus 2 poin
                bonus += (val / base_val) * 2.0
                
        # Base score is 100, subtract penalties, add bonuses
        scores = 100.0 - penalties + bonus
        scores = np.clip(scores, 0, 100) # clip between 0 and 100
        
        df['nutrition_score'] = scores
        return df

class NutritionFilter:
    def __init__(self, min_score=60.0, strict_limits=None):
        """
        Initialize the filter.
        min_score: Recipes below this nutrition_score are filtered out.
        strict_limits: Dict of hard upper limits (e.g. {'calories': 1500} implies reject > 1500 limit).
        """
        self.min_score = min_score
        self.strict_limits = strict_limits or {}
        
    def filter_recipes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter out recipes that do not meet the minimum nutritional criteria.
        Expects a DataFrame that already has 'nutrition_score'.
        """
        # First filter by overall score
        valid_df = df[df['nutrition_score'] >= self.min_score].copy()
        
        # Apply strict hard limits if any
        for nutrient, limit in self.strict_limits.items():
            if nutrient in valid_df.columns:
                valid_df = valid_df[valid_df[nutrient] <= limit]
                
        return valid_df

if __name__ == "__main__":
    # Test
    data = {
        'id': [1,2,3], 
        'calories': [20, 45, 10], 
        'sugar_pdv': [5, 50, 10],
        'protein_pdv': [20, 5, 25], # Added protein for bonus
        'portion_weight_g': [100, 200, 50] # Simulasi berat per porsi awal
    }
    df_test = pd.DataFrame(data)
    scorer = NutritionScorer()
    
    # Hitung dengan normalisasi ke 100g
    df_scored = scorer.calculate_score(df_test, weight_col='portion_weight_g')
    print("Scores:")
    print(df_scored)
    
    n_filter = NutritionFilter(min_score=80)
    print("\Filtered:")
    print(n_filter.filter_recipes(df_scored))
