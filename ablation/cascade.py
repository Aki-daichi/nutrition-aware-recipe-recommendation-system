# ablation/cascade.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class CFWrapper:
    def __init__(self, model):
        """
        Wraps a trained Collaborative Filtering model (e.g., NCFModel).
        """
        self.model = model

    def score_candidates(self, user_id: int, candidate_items: np.ndarray) -> np.ndarray:
        return self.model.score_candidates(user_id, candidate_items)

class CBFWrapper:
    def __init__(self, cbf_model, user_history, idx2item):
        """
        Wraps a content-based filtering model (e.g. TFIDFRecommender) using Max-Pooling similarity.
        user_history: Dict of user_id -> list of candidate CF indices (from train/val)
        idx2item: Dict of CF index -> original recipe ID
        """
        self.cbf = cbf_model
        self.user_history = user_history
        self.idx2item = idx2item
        self.mat = self.cbf.tfidf_matrix
        
        # Precompute valid history indices per user in CBF matrix
        self.valid_history = {}
        for u, items in self.user_history.items():
            valid_idx = []
            for cf_idx in items:
                real_id = self.idx2item.get(cf_idx)
                if real_id is not None and real_id in self.cbf.item_id_to_idx:
                    valid_idx.append(self.cbf.item_id_to_idx[real_id])
            if valid_idx:
                self.valid_history[u] = valid_idx

    def score_candidates(self, user_id: int, candidate_items: np.ndarray) -> np.ndarray:
        hist_idx = self.valid_history.get(user_id)
        if not hist_idx:
            # Return zeros if user has no history
            return np.zeros(len(candidate_items))
            
        cand_idx = []
        valid_mask = []
        for c in candidate_items:
            real_id = self.idx2item.get(c)
            if real_id is not None and real_id in self.cbf.item_id_to_idx:
                cand_idx.append(self.cbf.item_id_to_idx[real_id])
                valid_mask.append(True)
            else:
                cand_idx.append(0)  # dummy index
                valid_mask.append(False)
                
        # Cosine similarity between user history items and candidates
        hist_vecs = self.mat[hist_idx]
        cand_vecs = self.mat[cand_idx]
        sims = cosine_similarity(hist_vecs, cand_vecs)
        
        # Max similarity for each candidate
        scores = sims.max(axis=0)
        
        # Mask out candidates not in vocabulary
        scores = scores * np.array(valid_mask)
        return scores

class NutritionWrapper:
    def __init__(self, recipe_nutrition_scores, idx2item, min_score=60.0, mode='filter', weight=0.3):
        """
        Wraps the nutrition scorer and filter logic.
        recipe_nutrition_scores: Dict of original recipe ID -> float (0-100 score)
        idx2item: Dict of CF index -> original recipe ID
        min_score: Minimum nutrition score for filtering
        mode: 'filter' (hard filter) or 'rerank' (weighted sum blending similarity and nutrition)
        weight: Weight of nutrition score in 'rerank' mode (0.0 to 1.0)
        """
        self.nutrition_scores = recipe_nutrition_scores
        self.idx2item = idx2item
        self.min_score = min_score
        self.mode = mode
        self.weight = weight

    def score_candidates(self, user_id: int, candidate_items: np.ndarray, incoming_scores: np.ndarray) -> np.ndarray:
        # Get nutrition score for each candidate item
        scores = np.zeros(len(candidate_items))
        for idx, c in enumerate(candidate_items):
            real_id = self.idx2item.get(c)
            scores[idx] = self.nutrition_scores.get(real_id, 50.0) # default to average 50 if missing
            
        if self.mode == 'filter':
            final_scores = incoming_scores.copy()
            # Items with nutrition_score < min_score are filtered (score set to -1e9)
            mask = (scores < self.min_score) & (incoming_scores > -1e8)
            final_scores[mask] = -1e9
            return final_scores
        elif self.mode == 'rerank':
            # Blend normalized nutrition score (0-1) and incoming score
            norm_nutr = scores / 100.0
            
            # Compute blended scores
            final_scores = (1 - self.weight) * incoming_scores + self.weight * norm_nutr
            
            # Ensure filtered out items remain filtered out
            final_scores[incoming_scores <= -1e8] = -1e9
            return final_scores
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

class CascadingRecommender:
    def __init__(self, stages):
        """
        stages: List of dicts representing stages, e.g.:
        [
            {'wrapper': cf_wrapper, 'top_k': 50},
            {'wrapper': cbf_wrapper, 'top_k': 20},
            {'wrapper': nutrition_wrapper, 'top_k': 10}
        ]
        """
        self.stages = stages

    def score_candidates(self, user_id: int, candidate_items: np.ndarray) -> np.ndarray:
        final_scores = np.zeros(len(candidate_items))
        active_mask = np.ones(len(candidate_items), dtype=bool)
        
        for stage in self.stages:
            wrapper = stage['wrapper']
            top_k = stage.get('top_k', None)
            
            # 1. Get scores from this wrapper
            if isinstance(wrapper, NutritionWrapper):
                # Nutrition wrapper requires incoming scores for filtering/reranking
                stage_scores = wrapper.score_candidates(user_id, candidate_items, final_scores)
            else:
                stage_scores = np.zeros(len(candidate_items))
                if np.any(active_mask):
                    raw_scores = wrapper.score_candidates(user_id, candidate_items)
                    stage_scores = raw_scores
            
            # Mask out currently inactive candidates
            stage_scores[~active_mask] = -1e9
            
            # 2. Filter/re-rank: Keep only top K items among active candidates
            if top_k is not None and top_k < np.sum(active_mask):
                active_indices = np.where(active_mask)[0]
                active_scores = stage_scores[active_indices]
                
                # Get the indices that sort active scores in descending order
                sorted_active_idx = np.argsort(active_scores)[::-1]
                
                # Select top_k active candidates
                keep_active_idx = sorted_active_idx[:top_k]
                keep_global_idx = active_indices[keep_active_idx]
                
                # Update active mask
                new_active_mask = np.zeros(len(candidate_items), dtype=bool)
                new_active_mask[keep_global_idx] = True
                active_mask = new_active_mask
                
                # Re-apply mask to scores
                stage_scores[~active_mask] = -1e9
                
            final_scores = stage_scores
            
        return final_scores
