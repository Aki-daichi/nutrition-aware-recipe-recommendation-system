import sys
import torch
import pickle
import numpy as np
from pathlib import Path
sys.path.append("cf")

def load_cf(model_path: Path):
    model_dir = model_path.parent
    
    with open(model_path, "rb") as f:
        data = pickle.load(f)
    net = data["model"]._model
    net.eval()
    
    with open(model_dir / "user2idx.pkl", "rb") as f:
        user2idx = pickle.load(f)
    with open(model_dir / "item2idx.pkl", "rb") as f:
        item2idx = pickle.load(f)
    with open(model_dir / "idx2item.pkl", "rb") as f:
        idx2item = pickle.load(f)
    
    return net, user2idx, item2idx, idx2item

def score_candidates(net, user2idx, idx2item, user_id: int, top_k: int):
    if user_id not in user2idx:
        raise KeyError(user_id)
    
    u = user2idx[user_id]
    n_items = net.emb_i_gmf.num_embeddings  # use model's actual size, not mapping size
    
    u_tensor = torch.tensor([u] * n_items)
    i_tensor = torch.tensor(list(range(n_items)))
    
    with torch.no_grad():
        scores = net(u_tensor, i_tensor).squeeze().numpy()
    
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    return [
        {"recipe_id": idx2item[int(idx)], "cf_score": float(scores[idx])}
        for idx in top_indices
        if int(idx) in idx2item
    ]
