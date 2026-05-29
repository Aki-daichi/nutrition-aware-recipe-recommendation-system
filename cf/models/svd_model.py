"""
cf/models/svd_model.py
──────────────────────
SVD (Matrix Factorization) wrapper using `surprise` library.

This wrapper adapts surprise's explicit rating SVD to the implicit 
pipeline. Since our binary matrix has 1s for observed interactions, 
we train SVD predicting 1s (and sample some 0s as negatives to 
prevent the model from predicting 1 for everything, a common trick 
when adapting explicit models for implicit tasks).
"""

from __future__ import annotations
import numpy as np
import scipy.sparse as sp
import pandas as pd
import random

try:
    from surprise import Dataset, Reader, SVD
except ImportError as e:
    raise ImportError("Please install scikit-surprise: pip install scikit-surprise") from e


class SVDModel:
    """
    SVD wrapper for implicit data.

    Parameters
    ----------
    factors        : number of latent factors.
    lr_all         : learning rate.
    reg_all        : regularization parameter.
    epochs         : number of epochs.
    random_state   : random seed.
    num_neg_samples: how many negative samples per positive item during training 
                     (to treat as rating 0).
    """

    def __init__(
        self,
        factors: int = 50,
        lr_all: float = 0.005,
        reg_all: float = 0.02,
        epochs: int = 20,
        num_neg_samples: int = 2,
        random_state: int = 42,
    ) -> None:
        self.factors = factors
        self.lr_all = lr_all
        self.reg_all = reg_all
        self.epochs = epochs
        self.num_neg_samples = num_neg_samples
        self.random_state = random_state
        
        self._algo = None

    def fit(self, user_item_matrix: sp.csr_matrix) -> "SVDModel":
        """
        Train Surprise SVD on the sparse matrix.
        We inject negative samples because SVD expects explicit ratings.
        """
        users, items = user_item_matrix.nonzero()
        n_users, n_items = user_item_matrix.shape
        
        # Build positive samples (rating = 1.0)
        u_list, i_list, r_list = list(users), list(items), [1.0] * len(users)
        
        # Build negative samples (rating = 0.0)
        # Randomly sample unobserved interactions
        num_pos = len(users)
        num_neg = int(num_pos * self.num_neg_samples)
        
        # Simple negative sampling
        import random
        random.seed(self.random_state)
        
        for _ in range(num_neg):
            u = random.randint(0, n_users - 1)
            i = random.randint(0, n_items - 1)
            # Not checking if (u,i) is positive for speed, since matrix is highly sparse (~99.8%)
            # The collision chance is tiny, and it adds some noise regularization.
            u_list.append(u)
            i_list.append(i)
            r_list.append(0.0)
            
        df = pd.DataFrame({'u': u_list, 'i': i_list, 'r': r_list})
        reader = Reader(rating_scale=(0.0, 1.0))
        data = Dataset.load_from_df(df[['u', 'i', 'r']], reader)
        trainset = data.build_full_trainset()
        
        self._algo = SVD(
            n_factors=self.factors,
            lr_all=self.lr_all,
            reg_all=self.reg_all,
            n_epochs=self.epochs,
            random_state=self.random_state
        )
        
        self._algo.fit(trainset)
        print(f"[SVD] Trained — factors={self.factors}, lr={self.lr_all}, reg={self.reg_all}, epochs={self.epochs}")
        return self

    def score_candidates(self, user_id: int, candidate_items: np.ndarray) -> np.ndarray:
        if self._algo is None:
            raise RuntimeError("Model must be trained before calling score_candidates().")
            
        scores = []
        # Support vectorization behavior
        for item in candidate_items:
            # uid and iid usually strings in surprise but inner ids can work if we match how it mapped.
            # Surprise mapped our integers internally. We pass the integer directly since our pandas df had integer u and i.
            pred = self._algo.predict(uid=user_id, iid=item).est
            scores.append(pred)
        return np.array(scores)

    def get_params(self) -> dict:
        return {
            "factors": self.factors,
            "lr_all": self.lr_all,
            "reg_all": self.reg_all,
            "epochs": self.epochs,
            "num_neg_samples": self.num_neg_samples,
        }

    def __repr__(self) -> str:
        return f"SVDModel({self.get_params()})"