import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import scipy.sparse as sp

# Shared Paths
MODEL_DIR = Path(__file__).parent.parent / "outputs" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

class TFIDFRecommender:
    def __init__(self, max_features=5000):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=max_features,
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.item_ids = None
        self.item_id_to_idx = {}
        
    def fit(self, df: pd.DataFrame, text_col: str, id_col: str = 'id'):
        """
        Fit the TF-IDF vectorizer on the combined text column and store the matrix.
        """
        print(f"Fitting TF-IDF model on {len(df)} recipes...")
        # Drop rows with missing text
        df = df.dropna(subset=[text_col]).reset_index(drop=True)
        
        self.item_ids = df[id_col].values
        self.item_id_to_idx = {item_id: idx for idx, item_id in enumerate(self.item_ids)}
        
        self.tfidf_matrix = self.vectorizer.fit_transform(df[text_col])
        print(f"TF-IDF Matrix shape: {self.tfidf_matrix.shape}")
        
    def save(self, filepath: str):
        """Save the model and TF-IDF matrix."""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'vectorizer': self.vectorizer,
                'tfidf_matrix': self.tfidf_matrix,
                'item_ids': self.item_ids,
                'item_id_to_idx': self.item_id_to_idx
            }, f)
        print(f"Model saved to {filepath}")
            
    def load(self, filepath: str):
        """Load the model and TF-IDF matrix."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.vectorizer = data['vectorizer']
            self.tfidf_matrix = data['tfidf_matrix']
            self.item_ids = data['item_ids']
            self.item_id_to_idx = data['item_id_to_idx']
        print(f"Model loaded from {filepath}")
            
    def get_similar_items(self, item_id: int, top_k: int = 10) -> list:
        """
        Get top_k most similar items based on cosine similarity
        Returns a list of tuples: (similar_item_id, similarity_score)
        """
        if item_id not in self.item_id_to_idx:
            raise ValueError(f"Item ID {item_id} not found in vocabulary.")
            
        target_idx = self.item_id_to_idx[item_id]
        target_vec = self.tfidf_matrix[target_idx]
        
        # Compute cosine similarity between the target vector and all items
        sim_scores = cosine_similarity(target_vec, self.tfidf_matrix).flatten()
        
        # Get top indices (excluding target_idx itself)
        # Using partitioning for performance on large matrices
        if len(sim_scores) > top_k + 1:
            top_indices = np.argpartition(sim_scores, -(top_k+1))[-(top_k+1):]
            # Sort the top ones
            top_indices = top_indices[np.argsort(sim_scores[top_indices])[::-1]]
        else:
            top_indices = np.argsort(sim_scores)[::-1]
            
        results = []
        for idx in top_indices:
            if idx != target_idx and len(results) < top_k:
                results.append((self.item_ids[idx], sim_scores[idx]))
                
        return results

if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    
    from feature_extractor import load_recipes, extract_text_features
    print("Loading recipes...")
    df_raw = load_recipes()
    if not df_raw.empty:
        print("Extracting text features...")
        df_processed = extract_text_features(df_raw)
        
        recommender = TFIDFRecommender(max_features=5000)
        recommender.fit(df_processed, text_col='combined_text', id_col='id')
        
        save_path = MODEL_DIR / "tfidf_cbf_model.pkl"
        recommender.save(save_path)
        
        # Test similarity
        sample_id = recommender.item_ids[0]
        print(f"\nTesting similarity for recipe ID: {sample_id}")
        similars = recommender.get_similar_items(sample_id, top_k=5)
        for i, (sid, score) in enumerate(similars):
            print(f"{i+1}. Recipe {sid}: {score:.4f}")
    else:
        print("No data to run TF-IDF.")
