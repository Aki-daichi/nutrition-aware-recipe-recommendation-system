"""
cf/models/ncf_model.py
──────────────────────
Neural Collaborative Filtering (NCF) model using PyTorch.

Reference:
  He, X., Liao, L., Zhang, H., Nie, L., Hu, X., & Chua, T.-S. (2017).
  Neural Collaborative Filtering. WWW '17.
"""

from __future__ import annotations
import numpy as np
import scipy.sparse as sp
import math

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
except ImportError as e:
    raise ImportError("PyTorch is required for NCF: pip install torch") from e


class NCFDataset(Dataset):
    def __init__(self, u_tensor, i_tensor, r_tensor):
        self.u = u_tensor
        self.i = i_tensor
        self.r = r_tensor
        
    def __len__(self):
        return len(self.u)
    
    def __getitem__(self, idx):
        return self.u[idx], self.i[idx], self.r[idx]


class NCFNet(nn.Module):
    def __init__(self, n_users, n_items, gmf_factors=8, mlp_factors=8, mlp_layers=[32, 16, 8]):
        super(NCFNet, self).__init__()
        # GMF embeddings
        self.emb_u_gmf = nn.Embedding(n_users, gmf_factors)
        self.emb_i_gmf = nn.Embedding(n_items, gmf_factors)
        
        # MLP embeddings
        self.emb_u_mlp = nn.Embedding(n_users, mlp_factors)
        self.emb_i_mlp = nn.Embedding(n_items, mlp_factors)
        
        # MLP layers
        mlp_modules = []
        in_dim = mlp_factors * 2
        for out_dim in mlp_layers:
            mlp_modules.append(nn.Linear(in_dim, out_dim))
            mlp_modules.append(nn.ReLU())
            in_dim = out_dim
        self.mlp = nn.Sequential(*mlp_modules)
        
        # Final output layer
        self.affine = nn.Linear(gmf_factors + mlp_layers[-1], 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, u, i):
        # GMF pathway
        u_gmf = self.emb_u_gmf(u)
        i_gmf = self.emb_i_gmf(i)
        vec_gmf = torch.mul(u_gmf, i_gmf)
        
        # MLP pathway
        u_mlp = self.emb_u_mlp(u)
        i_mlp = self.emb_i_mlp(i)
        vec_mlp = torch.cat([u_mlp, i_mlp], dim=-1)
        vec_mlp = self.mlp(vec_mlp)
        
        # Combine
        vec_out = torch.cat([vec_gmf, vec_mlp], dim=-1)
        out = self.affine(vec_out)
        return self.sigmoid(out).squeeze()


class NCFModel:
    """
    NCF model wrapper compatible with evaluator pipeline.
    """

    def __init__(
        self,
        gmf_factors: int = 8,
        mlp_factors: int = 8,
        batch_size: int = 1024,
        lr: float = 0.001,
        epochs: int = 10,
        num_negatives: int = 4,
        random_state: int = 42,
    ) -> None:
        self.gmf_factors = gmf_factors
        self.mlp_factors = mlp_factors
        self.batch_size = batch_size
        self.lr = lr
        self.epochs = epochs
        self.num_negatives = num_negatives
        self.random_state = random_state
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = None
        
    def fit(self, user_item_matrix: sp.csr_matrix) -> "NCFModel":
        n_users, n_items = user_item_matrix.shape
        self._model = NCFNet(
            n_users, n_items, 
            gmf_factors=self.gmf_factors, 
            mlp_factors=self.mlp_factors
        ).to(self.device)
        
        # Generate training dataset with negatives
        users, items = user_item_matrix.nonzero()
        
        u_list, i_list, r_list = list(users), list(items), [1.0] * len(users)
        num_neg = int(len(users) * self.num_negatives)
        
        np.random.seed(self.random_state)
        # Random uniform negative sampling
        neg_users = np.random.randint(0, n_users, num_neg)
        neg_items = np.random.randint(0, n_items, num_neg)
        
        u_list.extend(neg_users)
        i_list.extend(neg_items)
        r_list.extend([0.0] * num_neg)
        
        dataset = NCFDataset(
            torch.tensor(u_list, dtype=torch.long),
            torch.tensor(i_list, dtype=torch.long),
            torch.tensor(r_list, dtype=torch.float32)
        )
        
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self._model.parameters(), lr=self.lr)
        
        print(f"[NCF] Mulai Training (Device: {self.device})")
        self._model.train()
        for epoch in range(self.epochs):
            total_loss = 0.0
            for u_b, i_b, r_b in loader:
                u_b, i_b, r_b = u_b.to(self.device), i_b.to(self.device), r_b.to(self.device)
                
                optimizer.zero_grad()
                preds = self._model(u_b, i_b)
                # Handle single element batch dim issue
                if len(preds.shape) == 0:
                    preds = preds.unsqueeze(0)
                loss = criterion(preds, r_b)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            # print(f"  Epoch {epoch+1}/{self.epochs} Loss: {total_loss/len(loader):.4f}")
            
        print(f"[NCF] Selesai — epochs={self.epochs}, lr={self.lr}")
        return self

    def score_candidates(self, user_id: int, candidate_items: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Model must be trained before calling score_candidates().")
            
        self._model.eval()
        with torch.no_grad():
            u_t = torch.tensor([user_id] * len(candidate_items), dtype=torch.long).to(self.device)
            i_t = torch.tensor(candidate_items, dtype=torch.long).to(self.device)
            preds = self._model(u_t, i_t).cpu().numpy()
        return preds

    def get_params(self) -> dict:
        return {
            "gmf_factors": self.gmf_factors,
            "mlp_factors": self.mlp_factors,
            "batch_size": self.batch_size,
            "lr": self.lr,
            "epochs": self.epochs,
            "num_negatives": self.num_negatives,
        }

    def __repr__(self) -> str:
        return f"NCFModel({self.get_params()})"