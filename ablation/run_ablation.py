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

# Setup mock modules for missing dependencies (implicit, surprise) to prevent ImportError
from unittest.mock import MagicMock

class MockImplicitModule(MagicMock):
    __version__ = "0.7.2"

sys.modules["implicit"] = MockImplicitModule()
sys.modules["implicit.als"] = MagicMock()
sys.modules["implicit.bpr"] = MagicMock()

mock_surprise = MagicMock()
sys.modules["surprise"] = mock_surprise

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
from ablation.cascade import CFWrapper, CBFWrapper, NutritionWrapper, CascadingRecommender, WeightedHybridRecommender


def evaluate_loo_with_nutrition(
    model,
    loo_data,
    idx2item,
    recipe_nutrition_scores,
    k_values=(5, 10, 20),
    verbose=True
):
    from cf.evaluator import hit_at_k, reciprocal_rank
    buckets = {f"HR@{k}": [] for k in k_values}
    buckets["MRR"] = []
    buckets["Avg_Nutrition"] = []

    n = len(loo_data)
    report_every = max(1, n // 5)

    for idx, entry in enumerate(loo_data):
        u          = entry["u"]
        candidates = entry["candidates"]   # np.ndarray, shape (1 + n_neg,)
        label_idx  = entry["label_idx"]    # position of pos_item in candidates

        # Get scores from model
        scores = model.score_candidates(u, candidates)  # shape: (n_candidates,)

        # Rank by descending score → list of candidate positions
        ranked_positions = np.argsort(scores)[::-1].tolist()

        # Accumulate metrics
        for k in k_values:
            buckets[f"HR@{k}"].append(hit_at_k(ranked_positions, label_idx, k))
        buckets["MRR"].append(reciprocal_rank(ranked_positions, label_idx))
        
        # Calculate nutrition score of top 10 recommended recipes
        top_10_cf_idxs = [candidates[pos] for pos in ranked_positions[:10]]
        top_10_recipe_ids = [idx2item.get(c) for c in top_10_cf_idxs]
        top_10_nutrition = [recipe_nutrition_scores.get(rid, 50.0) for rid in top_10_recipe_ids if rid is not None]
        avg_nutr = np.mean(top_10_nutrition) if top_10_nutrition else 50.0
        buckets["Avg_Nutrition"].append(avg_nutr)

        if verbose and (idx + 1) % report_every == 0:
            pct = (idx + 1) / n * 100
            print(f"  Evaluating… {idx+1:,}/{n:,} ({pct:.0f}%)")

    results = {key: float(np.mean(vals)) for key, vals in buckets.items()}
    return results

def custom_metrics_to_dataframe(results: dict[str, dict]) -> pd.DataFrame:
    rows = []
    for model_name, metrics in results.items():
        row = {"Model": model_name}
        row.update(metrics)
        rows.append(row)
    df = pd.DataFrame(rows).set_index("Model")
    ordered_cols = ["HR@5", "HR@10", "HR@20", "MRR", "Avg_Nutrition"]
    # Keep only columns that exist
    ordered_cols = [c for c in ordered_cols if c in df.columns]
    return df[ordered_cols]

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
    
    # 6.2 Define Weighted Hybrid configurations (grid search)
    weight_configs = []
    # Generasi bobot w_cf dari 0.4 s.d 1.0, w_cbf dan w_nutr menyesuaikan (sum to 1.0)
    for cf_w_int in range(4, 11):
        w_cf = cf_w_int / 10.0
        remaining = round(1.0 - w_cf, 1)
        for cbf_w_int in range(0, int(remaining * 10) + 1):
            w_cbf = cbf_w_int / 10.0
            w_nutr = round(remaining - w_cbf, 1)
            weight_configs.append((w_cf, w_cbf, w_nutr))

    for w_cf, w_cbf, w_nutr in weight_configs:
        hybrid_recommender = WeightedHybridRecommender(
            cf_wrapper=cf_wrapper,
            cbf_wrapper=cbf_wrapper,
            nutrition_scores=recipe_nutrition_scores,
            idx2item=idx2item,
            w_cf=w_cf,
            w_cbf=w_cbf,
            w_nutr=w_nutr
        )
        configurations.append({
            "name": f"Hybrid (cf={w_cf:.1f}, cbf={w_cbf:.1f}, nutr={w_nutr:.1f})",
            "model": hybrid_recommender
        })

    # 7. Evaluate each configuration
    all_results = {}
    
    print("\nStarting evaluation of ablation study configurations...")
    for config in configurations:
        name = config["name"]
        stages = config.get("stages")
        
        print(f"\nEvaluating: {name}")
        # Build Cascading model if stages is specified, else use the model directly
        if stages is not None:
            model = CascadingRecommender(stages)
        else:
            model = config["model"]
        
        start_time = time.time()
        # Run LOO evaluation with nutrition
        metrics = evaluate_loo_with_nutrition(
            model, 
            loo_data, 
            idx2item, 
            recipe_nutrition_scores, 
            k_values=(5, 10, 20), 
            verbose=True
        )
        elapsed = time.time() - start_time
        
        all_results[name] = metrics
        print(f"Done in {elapsed:.1f}s. HR@10: {metrics['HR@10']:.4f} | MRR: {metrics['MRR']:.4f} | Avg Nutrition: {metrics['Avg_Nutrition']:.4f}")
        
    # 8. Export metrics
    results_df = custom_metrics_to_dataframe(all_results)
    
    print("\n" + "=" * 75)
    print("                    ABLATION STUDY METRIC RESULTS")
    print("=" * 75)
    print(results_df.to_string(float_format=lambda x: f"{x:.4f}"))
    print("=" * 75)
    
    # Save output
    output_results_dir = PROJECT_ROOT / "ablation" / "outputs" / "results"
    output_results_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_results_dir / "ablation_study_results.csv"
    results_df.to_csv(csv_file)
    print(f"\nSuccessfully exported ablation study metrics to:\n  {csv_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
