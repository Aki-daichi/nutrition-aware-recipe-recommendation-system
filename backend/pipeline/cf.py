from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch


@dataclass
class CFArtifacts:
    model: Any
    user_mapping: dict[int, int]
    item_mapping: dict[int, int]
    device: torch.device


def _load_pickle(path: Path):
    with open(path, "rb") as f:
        return pickle.load(f)


def load_cf(model_dir: Path) -> CFArtifacts:
    """CF loader.

    This capstone repo does not ship user/item mapping pickles needed for NCF inference.
    We load the model checkpoint if present, but CF scoring will use a DB-based fallback
    (see `cf_fallback_candidates`) instead of NCF.
    """

    # Optional: try to load a model artifact if it exists.
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # In this repo the trained artifact is stored as a pickle under cf/outputs/models
    model_candidate_paths = [
        model_dir / "cf" / "ncf_model.pt",
        model_dir / "cf" / "outputs" / "models" / "best_cf_model_ncf.pkl",
    ]
    model_path = next((p for p in model_candidate_paths if p.exists()), None)

    model = None
    if model_path is not None:
        # best-effort load; if it fails we still run fallback CF.
        try:
            model = torch.load(model_path, map_location=device)
            if hasattr(model, "eval"):
                model.eval()
        except Exception:
            model = None

    # Mappings are not available; return empty mappings.
    user_mapping: dict[int, int] = {}
    item_mapping: dict[int, int] = {}

    return CFArtifacts(model=model, user_mapping=user_mapping, item_mapping=item_mapping, device=device)


def cf_fallback_candidates(interactions_rows: list[dict[str, Any]], user_id: int, top_n: int) -> list[dict[str, Any]]:
    """Fallback CF stage using interaction ratings only.

    Logic: compute weighted average rating per candidate recipe from similar users.
    For simplicity/demo: we treat "similar" as users who have rated at least one common recipe
    with the target user.

    Returns list of {recipe_id, cf_score}.
    """
    # Interactions rows already fetched from DB; structure: {user_id, recipe_id, rating}

    target_ratings = [r for r in interactions_rows if int(r["user_id"]) == int(user_id) and float(r.get("rating") or 0) > 0]
    if not target_ratings:
        # No positive history: return top recipes by global average rating
        from collections import defaultdict

        sums = defaultdict(float)
        cnts = defaultdict(int)
        for r in interactions_rows:
            rating = float(r.get("rating") or 0)
            if rating > 0:
                rid = int(r["recipe_id"])
                sums[rid] += rating
                cnts[rid] += 1

        scored = []
        for rid, s in sums.items():
            scored.append({"recipe_id": rid, "cf_score": float(s / max(cnts[rid], 1))})
        scored.sort(key=lambda x: x["cf_score"], reverse=True)
        return scored[: top_n * 10]

    target_recipe_ids = {int(r["recipe_id"]) for r in target_ratings}

    # Find similar users: users who share at least one rated recipe with target
    from collections import defaultdict

    user_shared = defaultdict(set)  # other_user -> shared recipe ids
    for r in interactions_rows:
        rating = float(r.get("rating") or 0)
        if rating <= 0:
            continue
        rid = int(r["recipe_id"])
        uid = int(r["user_id"])
        if uid == int(user_id):
            continue
        if rid in target_recipe_ids:
            user_shared[uid].add(rid)

    similar_users = {uid for uid, shared in user_shared.items() if len(shared) > 0}

    sums = defaultdict(float)
    cnts = defaultdict(int)
    for r in interactions_rows:
        rating = float(r.get("rating") or 0)
        if rating <= 0:
            continue
        uid = int(r["user_id"])
        if uid not in similar_users:
            continue
        rid = int(r["recipe_id"])
        if rid in target_recipe_ids:
            continue
        sums[rid] += rating
        cnts[rid] += 1

    scored = []
    for rid, s in sums.items():
        scored.append({"recipe_id": rid, "cf_score": float(s / max(cnts[rid], 1))})

    if not scored:
        # fallback to global
        sums = defaultdict(float)
        cnts = defaultdict(int)
        for r in interactions_rows:
            rating = float(r.get("rating") or 0)
            if rating > 0:
                rid = int(r["recipe_id"])
                sums[rid] += rating
                cnts[rid] += 1
        for rid, s in sums.items():
            if rid in target_recipe_ids:
                continue
            scored.append({"recipe_id": rid, "cf_score": float(s / max(cnts[rid], 1))})

    scored.sort(key=lambda x: x["cf_score"], reverse=True)
    return scored[: top_n * 10]



@torch.no_grad()
def score_candidates(cf: CFArtifacts, user_id: int, top_k: int) -> list[dict[str, Any]]:
    """Stage 1 CF: return top candidates with cf_score."""
    if user_id not in cf.user_mapping:
        raise KeyError(user_id)

    u = cf.user_mapping[user_id]

    # candidate item indices are [0..n_items-1] inferred from item_mapping
    item_indices = np.arange(len(cf.item_mapping), dtype=np.int64)

    # Model scoring
    # Assumes model forward signature like model(u_tensor, i_tensor) and returns probabilities.
    u_t = torch.tensor(np.full_like(item_indices, u), dtype=torch.long, device=cf.device)
    i_t = torch.tensor(item_indices, dtype=torch.long, device=cf.device)

    preds = cf.model(u_t, i_t)
    if isinstance(preds, torch.Tensor):
        preds_np = preds.detach().cpu().numpy()
    else:
        preds_np = np.asarray(preds)

    # top_k
    if top_k >= len(preds_np):
        top_idx = np.argsort(preds_np)[::-1]
    else:
        top_idx = np.argpartition(preds_np, -top_k)[-top_k:]
        top_idx = top_idx[np.argsort(preds_np[top_idx])[::-1]]

    # Need reverse mapping idx->recipe_id
    idx_to_item = {idx: rid for rid, idx in cf.item_mapping.items()}

    results = []
    for idx in top_idx:
        rid = idx_to_item.get(int(idx))
        if rid is None:
            continue
        results.append({"recipe_id": int(rid), "cf_score": float(preds_np[int(idx)])})
    return results

