# ablation/run_ablation.py
import os
import sys
import pickle
import time
from pathlib import Path
import numpy as np
import pandas as pd

# Setup Python paths to resolve project components
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# To resolve the conflict where both cf and cbf have folders named 'models'
# we pre-import the cf models and register them in sys.modules as 'models.*'
import cf.models.ncf_model as cf_ncf
import cf.models.als_model as cf_als
import cf.models.bpr_model as cf_bpr
import cf.models.svd_model as cf_svd
sys.modules['models.ncf_model'] = cf_ncf
sys.modules['models.als_model'] = cf_als
sys.modules['models.bpr_model'] = cf_bpr
sys.modules['models.svd_model'] = cf_svd
sys.modules['models'] = sys.modules['cf.models']

from cf.data_prep import load_cf_splits, build_user_history, prepare_loo_eval, get_matrix_dims
from cf.evaluator import evaluate_loo, metrics_to_dataframe
from cbf.models.tfidf_model import TFIDFRecommender
from cbf.nutrition_extractor import extract_nutrition_features
from nutrition.scoring import NutritionScorer

# Import our cascading module
from ablation.cascade import CFWrapper, CBFWrapper, NutritionWrapper, CascadingRecommender

def main():
    print("=" * 60)
    print("     STARTING CASCADING MODEL ABLATION STUDY")
    print("=" * 60)
    
    # 1. Loading indices and mappings
    split_dir = PROJECT_ROOT / "cf" / "outputs" / "cf_split"
    print(f"Loading user/item index mappings from {split_dir}...")
    
    with open(split_dir / "idx2item.pkl", "rb") as f:
        idx2item = pickle.load(f)
    with open(split_dir / "item2idx.pkl", "rb") as f:
        item2idx = pickle.load(f)
        
    # 2. Loading dataset splits
    print("\nLoading dataset splits...")
    cf_train, cf_val, cf_test = load_cf_splits()
    n_users, n_items = get_matrix_dims(cf_train, cf_val, cf_test)
    
    # Build user histories (items interacted with during train + val)
    user_history = build_user_history(cf_train, cf_val)
    
    # Prepare Leave-One-Out test set (1 positive, 99 negatives)
    print("\nPreparing Leave-One-Out test evaluation records...")
    loo_data = prepare_loo_eval(cf_test, user_history, n_items, n_negatives=99, seed=42)
    
    # 3. Load pre-trained models
    # 3.1 Load CF model
    cf_model_path = PROJECT_ROOT / "cf" / "outputs" / "models" / "best_cf_model_ncf.pkl"
    print(f"\nLoading best CF model from {cf_model_path}...")
    with open(cf_model_path, "rb") as f:
        cf_data = pickle.load(f)
    print(f"Loaded CF model type: {cf_data['name']}")
    cf_model = cf_data['model']
    
    # 3.2 Load CBF model
    cbf_model_path = PROJECT_ROOT / "cbf" / "outputs" / "models" / "best_cbf_model_tfidf.pkl"
    print(f"Loading best CBF TF-IDF model from {cbf_model_path}...")
    cbf_model = TFIDFRecommender()
    cbf_model.load(str(cbf_model_path))
    
    # 4. Extract and calculate recipe nutrition scores
    print("\nExtracting and pre-calculating recipe nutrition scores...")
    try:
        raw_recipes_path = PROJECT_ROOT / "dataset" / "RAW_recipes_cleaned.csv"
        if not raw_recipes_path.exists():
            raw_recipes_path = PROJECT_ROOT / "dataset" / "RAW_recipes.csv"
        
        print(f"Reading recipe data from {raw_recipes_path}...")
        df_recipes = pd.read_csv(raw_recipes_path)
        
        # Align with CF split
        df_recipes = df_recipes[df_recipes['id'].isin(item2idx.keys())].copy()
        
        # Parse nutrition array columns
        df_recipes = extract_nutrition_features(df_recipes)
        
        # Calculate health scores using NutritionScorer
        scorer = NutritionScorer()
        df_recipes = scorer.calculate_score(df_recipes)
        
        recipe_nutrition_scores = dict(zip(df_recipes['id'], df_recipes['nutrition_score']))
        print(f"Successfully calculated nutrition scores for {len(recipe_nutrition_scores)} recipes.")
    except Exception as e:
        print(f"Warning: Could not calculate nutrition scores: {e}. Defaulting all recipes to a score of 50.0")
        recipe_nutrition_scores = {}

    # 5. Initialize stage wrappers
    cf_wrapper = CFWrapper(cf_model)
    cbf_wrapper = CBFWrapper(cbf_model, user_history, idx2item)
    nutr_filter_wrapper = NutritionWrapper(recipe_nutrition_scores, idx2item, min_score=60.0, mode='filter')
    nutr_rerank_wrapper = NutritionWrapper(recipe_nutrition_scores, idx2item, mode='rerank', weight=0.3)
    
    # 6. Define ablation configurations
    configurations = [
        {
            "name": "1. Pure CF (NCF)",
            "stages": [
                {"wrapper": cf_wrapper, "top_k": 100}
            ]
        },
        {
            "name": "2. Pure CBF (TF-IDF)",
            "stages": [
                {"wrapper": cbf_wrapper, "top_k": 100}
            ]
        },
        {
            "name": "3. Cascade CF -> CBF (k=50)",
            "stages": [
                {"wrapper": cf_wrapper, "top_k": 50},
                {"wrapper": cbf_wrapper, "top_k": 10}
            ]
        },
        {
            "name": "4. Cascade CF -> CBF (k=20)",
            "stages": [
                {"wrapper": cf_wrapper, "top_k": 20},
                {"wrapper": cbf_wrapper, "top_k": 10}
            ]
        },
        {
            "name": "5. Cascade CBF -> CF (k=50)",
            "stages": [
                {"wrapper": cbf_wrapper, "top_k": 50},
                {"wrapper": cf_wrapper, "top_k": 10}
            ]
        },
        {
            "name": "6. Cascade CBF -> CF (k=20)",
            "stages": [
                {"wrapper": cbf_wrapper, "top_k": 20},
                {"wrapper": cf_wrapper, "top_k": 10}
            ]
        },
        {
            "name": "7. Cascade CF -> CBF -> Nutrition Filter (k=50, 20)",
            "stages": [
                {"wrapper": cf_wrapper, "top_k": 50},
                {"wrapper": cbf_wrapper, "top_k": 20},
                {"wrapper": nutr_filter_wrapper, "top_k": 10}
            ]
        },
        {
            "name": "8. Cascade CF -> CBF -> Nutrition Rerank (k=50, 20)",
            "stages": [
                {"wrapper": cf_wrapper, "top_k": 50},
                {"wrapper": cbf_wrapper, "top_k": 20},
                {"wrapper": nutr_rerank_wrapper, "top_k": 10}
            ]
        }
    ]
    
    # 7. Evaluate each configuration
    all_results = {}
    
    print("\nStarting evaluation of ablation study configurations...")
    for config in configurations:
        name = config["name"]
        stages = config["stages"]
        
        print(f"\nEvaluating: {name}")
        # Build Cascading model
        model = CascadingRecommender(stages)
        
        start_time = time.time()
        # Run LOO evaluation
        metrics = evaluate_loo(model, loo_data, k_values=(5, 10, 20), verbose=True)
        elapsed = time.time() - start_time
        
        all_results[name] = metrics
        print(f"Done in {elapsed:.1f}s. HR@10: {metrics['HR@10']:.4f} | MRR: {metrics['MRR']:.4f}")
        
    # 8. Export metrics
    results_df = metrics_to_dataframe(all_results)
    
    print("\n" + "=" * 70)
    print("                    ABLATION STUDY METRIC RESULTS")
    print("=" * 70)
    print(results_df.to_string(float_format=lambda x: f"{x:.4f}"))
    print("=" * 70)
    
    # Save output
    output_results_dir = PROJECT_ROOT / "cf" / "outputs" / "results"
    output_results_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_results_dir / "ablation_study_results.csv"
    results_df.to_csv(csv_file)
    print(f"\nSuccessfully exported ablation study metrics to:\n  {csv_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
