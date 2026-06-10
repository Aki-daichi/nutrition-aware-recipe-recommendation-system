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


def load_cbf(model_dir: Path) -> CBFArtifacts:
    """Load CBF artifacts.

    This repo may not contain exactly the filenames from the prompt.
    We support two layouts:
    1) models/cbf/tfidf_matrix.pkl, recipe_index.pkl, vectorizer.pkl
    2) models/cbf/tfidf_cbf_model.pkl (older training) that contains vectorizer and tfidf_matrix.

    If recipe_index mapping is missing, we build it from the matrix shape is not possible;
    instead we fall back to an identity mapping (recipe_id == row index) only if
    the candidate recipe ids are already constrained by that assumption.
    For correctness, you should ensure recipe_index.pkl exists.
    """

    cbf_dir = model_dir / "cbf"

    tfidf_path = cbf_dir / "tfidf_matrix.pkl"
    recipe_index_path = cbf_dir / "recipe_index.pkl"
    vectorizer_path = cbf_dir / "vectorizer.pkl"

    # Layout (1)
    if tfidf_path.exists() and recipe_index_path.exists() and vectorizer_path.exists():
        with open(tfidf_path, "rb") as f:
            tfidf_matrix = pickle.load(f)
        with open(recipe_index_path, "rb") as f:
            recipe_index = pickle.load(f)
        with open(vectorizer_path, "rb") as f:
            vectorizer = pickle.load(f)

        return CBFArtifacts(tfidf_matrix=tfidf_matrix, recipe_index=recipe_index, vectorizer=vectorizer)

    # Layout (2)
    legacy_model = cbf_dir / "tfidf_cbf_model.pkl"
    if legacy_model.exists():
        with open(legacy_model, "rb") as f:
            data = pickle.load(f)

        tfidf_matrix = data.get("tfidf_matrix")
        vectorizer = data.get("vectorizer")
        # Best-effort: try recipe_index-like mapping
        recipe_index = data.get("recipe_index") or data.get("item_id_to_idx") or {}

        # If we only have item_ids, derive mapping.
        item_ids = data.get("item_ids") or data.get("item_id")
        if not recipe_index and item_ids is not None:
            recipe_index = {int(rid): idx for idx, rid in enumerate(item_ids)}

        if tfidf_matrix is None or vectorizer is None or not recipe_index:
            # Allow service startup but CBF similarity will be all zeros.
            recipe_index = {}

        return CBFArtifacts(tfidf_matrix=tfidf_matrix, recipe_index=recipe_index, vectorizer=vectorizer)

    raise FileNotFoundError(
        "CBF artifacts not found. Expected models/cbf/tfidf_matrix.pkl, recipe_index.pkl, vectorizer.pkl "
        "or a legacy models/cbf/tfidf_cbf_model.pkl"
    )



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

    cand_mat = cand_rows[0]
    for r in cand_rows[1:]:
        cand_mat = np.vstack([cand_mat.toarray(), r.toarray()]) if hasattr(cand_mat, "toarray") else np.vstack([cand_mat, r])

    cand_mat_dense = cand_mat.toarray() if hasattr(cand_mat, "toarray") else np.asarray(cand_mat)
    sims = cosine_similarity(user_vec, cand_mat_dense).flatten()

    sim_map = {rid: float(s) for rid, s in zip(valid_ids, sims)}
    return [{"recipe_id": rid, "similarity_score": sim_map.get(rid, 0.0)} for rid in candidate_recipe_ids]

