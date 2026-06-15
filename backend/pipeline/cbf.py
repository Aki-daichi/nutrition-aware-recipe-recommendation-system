from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class CBFArtifacts:
    tfidf_matrix: Any  # expected scipy sparse matrix
    recipe_index: dict[int, int]  # recipe_id -> row index
    vectorizer: Any


def load_cbf(model_path: Path) -> CBFArtifacts:
    """Load CBF artifacts from a direct file path.

    The model file is expected to be a pickle file containing a dictionary with:
    - 'tfidf_matrix'
    - 'vectorizer'
    - 'recipe_index' or 'item_id_to_idx'
    """
    if not model_path.exists():
        raise FileNotFoundError(f"CBF model file not found at: {model_path}")

    with open(model_path, "rb") as f:
        data = pickle.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected model pickle to be a dictionary, got {type(data)}")

    tfidf_matrix = data.get("tfidf_matrix")
    vectorizer = data.get("vectorizer")
    # Best-effort: try recipe_index-like mapping
    recipe_index = data.get("recipe_index")
    if recipe_index is None:
        recipe_index = data.get("item_id_to_idx")
    if recipe_index is None:
        recipe_index = {}

    # If we only have item_ids, derive mapping.
    item_ids = data.get("item_ids")
    if item_ids is None:
        item_ids = data.get("item_id")

    if not recipe_index and item_ids is not None:
        recipe_index = {int(rid): idx for idx, rid in enumerate(item_ids)}

    if tfidf_matrix is None or vectorizer is None or not recipe_index:
        # Allow service startup but CBF similarity will be all zeros.
        recipe_index = {}

    return CBFArtifacts(tfidf_matrix=tfidf_matrix, recipe_index=recipe_index, vectorizer=vectorizer)



def build_user_profile_vector(cbf: CBFArtifacts, past_recipe_ids: list[int]) -> NDArray[np.float64] | None:
    if not past_recipe_ids:
        return None

    indices = [cbf.recipe_index[rid] for rid in past_recipe_ids if rid in cbf.recipe_index]
    if not indices:
        return None

    # average of past recipe tfidf rows
    user_vec = cbf.tfidf_matrix[indices]
    # if sparse: keep as dense for cosine_similarity
    user_vec_mean = user_vec.mean(axis=0)
    return np.asarray(user_vec_mean).reshape(1, -1)


def score_cbf(cbf: CBFArtifacts, candidate_recipe_ids: list[int], past_recipe_ids: list[int]) -> list[dict[str, Any]]:
    user_vec = build_user_profile_vector(cbf, past_recipe_ids)
    if user_vec is None:
        # no history -> similarity 0
        return [{"recipe_id": rid, "similarity_score": 0.0} for rid in candidate_recipe_ids]

    # get candidate vectors
    cand_rows = []
    valid_ids = []
    for rid in candidate_recipe_ids:
        if rid in cbf.recipe_index:
            cand_rows.append(cbf.tfidf_matrix[cbf.recipe_index[rid]])
            valid_ids.append(rid)

    if not cand_rows:
        return [{"recipe_id": rid, "similarity_score": 0.0} for rid in candidate_recipe_ids]

    cand_mat = np.vstack([
        r.toarray() if hasattr(r, "toarray") else np.asarray(r).reshape(1, -1)
        for r in cand_rows
    ])

    cand_mat_dense = cand_mat.toarray() if hasattr(cand_mat, "toarray") else np.asarray(cand_mat)
    sims = cosine_similarity(user_vec, cand_mat_dense).flatten()

    sim_map = {rid: float(s) for rid, s in zip(valid_ids, sims)}
    return [{"recipe_id": rid, "similarity_score": sim_map.get(rid, 0.0)} for rid in candidate_recipe_ids]

