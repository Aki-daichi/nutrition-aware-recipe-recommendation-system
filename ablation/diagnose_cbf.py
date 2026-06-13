# -*- coding: utf-8 -*-
# ablation/diagnose_cbf.py
"""
Diagnostik kuantitatif untuk menganalisis penyebab performa CBF yang buruk.
Menguji 4 hipotesis utama:
  H1: Coverage -- apakah item test punya representasi CBF?
  H2: Discriminability -- skor positif vs negatif seberapa beda?
  H3: User history length -- apakah makin panjang history makin baik?
  H4: Sparsity bahan -- seberapa mirip antar resep secara umum?
"""

import sys
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import cf.models.ncf_model
import cf.models.als_model
import cf.models.bpr_model
import cf.models.svd_model
sys.modules['models.ncf_model'] = cf.models.ncf_model
sys.modules['models.als_model'] = cf.models.als_model
sys.modules['models.bpr_model'] = cf.models.bpr_model
sys.modules['models.svd_model'] = cf.models.svd_model
sys.modules['models'] = sys.modules['cf.models']

from cf.data_prep import load_cf_splits, build_user_history, prepare_loo_eval, get_matrix_dims
from cbf.models.tfidf_model import TFIDFRecommender

SEP = "-" * 65
SEP2 = "=" * 65

SPLIT_DIR = PROJECT_ROOT / "cf" / "outputs" / "cf_split"
CBF_MODEL_PATH = PROJECT_ROOT / "cbf" / "outputs" / "models" / "best_cbf_model_tfidf.pkl"

print(SEP2)
print("    DIAGNOSTIK: Mengapa CBF (Ingredients) Buruk?")
print(SEP2)

# Load data
print("\n[SETUP] Memuat data...")
with open(SPLIT_DIR / "idx2item.pkl", "rb") as f:
    idx2item = pickle.load(f)
with open(SPLIT_DIR / "item2idx.pkl", "rb") as f:
    item2idx = pickle.load(f)

cf_train, cf_val, cf_test = load_cf_splits()
n_users, n_items = get_matrix_dims(cf_train, cf_val, cf_test)
user_history = build_user_history(cf_train, cf_val)

cbf_model = TFIDFRecommender()
cbf_model.load(str(CBF_MODEL_PATH))

loo_data = prepare_loo_eval(cf_test, user_history, n_items, n_negatives=99, seed=42)
idx2cbf = {cf_idx: cbf_model.item_id_to_idx[rid]
           for cf_idx, rid in idx2item.items()
           if rid in cbf_model.item_id_to_idx}

print(f"Total LOO records              : {len(loo_data):,}")
print(f"Items dengan representasi CBF  : {len(idx2cbf):,} / {n_items:,} "
      f"({len(idx2cbf)/n_items*100:.1f}%)")

# =========================================================================
# H1: Coverage -- apakah cosine similarity item test ke history mendekati 0?
# =========================================================================
print("\n" + SEP)
print("H1: Coverage & Similarity -- seberapa dekat item test ke history user")
print(SEP)

n_sample = min(500, len(loo_data))
sample_loo = loo_data[:n_sample]

total_sim_pos, zero_history = [], 0
for entry in sample_loo:
    u = entry["u"]
    pos_item = entry["pos_item"]

    if pos_item not in idx2cbf:
        continue
    hist_cbf = [idx2cbf[i] for i in user_history.get(u, []) if i in idx2cbf]
    if not hist_cbf:
        zero_history += 1
        continue

    pos_cbf_idx = idx2cbf[pos_item]
    hist_vecs = cbf_model.tfidf_matrix[hist_cbf]
    pos_vec   = cbf_model.tfidf_matrix[pos_cbf_idx]
    sims = cosine_similarity(hist_vecs, pos_vec).flatten()
    total_sim_pos.append(sims.max())

sims_arr = np.array(total_sim_pos)
print(f"  Users dengan empty CBF history     : {zero_history} / {n_sample} "
      f"({zero_history/n_sample*100:.1f}%)")
print(f"  Rata-rata max cosine (hist -> pos)  : {sims_arr.mean():.4f}")
print(f"  Median max cosine                  : {np.median(sims_arr):.4f}")
print(f"  % item test dengan sim > 0.3       : {np.mean(sims_arr > 0.3)*100:.1f}%")
print(f"  % item test dengan sim > 0.5       : {np.mean(sims_arr > 0.5)*100:.1f}%")
print(f"  % item test dengan sim = 0         : {np.mean(sims_arr == 0)*100:.1f}%")

# =========================================================================
# H2: Discriminability -- skor positif vs negatif
# =========================================================================
print("\n" + SEP)
print("H2: Discriminability -- similarity positif vs negatif (1 pos vs 99 neg)")
print(SEP)

pos_scores_all, neg_scores_all = [], []
pos_beat_neg, total_valid = 0, 0

for entry in sample_loo:
    u = entry["u"]
    pos_item  = entry["pos_item"]
    candidates = entry["candidates"]
    label_idx  = entry["label_idx"]

    if pos_item not in idx2cbf:
        continue
    hist_cbf = [idx2cbf[i] for i in user_history.get(u, []) if i in idx2cbf]
    if not hist_cbf:
        continue

    cand_cbf   = [idx2cbf.get(c) for c in candidates]
    valid_mask = [i is not None for i in cand_cbf]
    cand_valid = [i for i in cand_cbf if i is not None]
    if not cand_valid:
        continue

    hist_vecs = cbf_model.tfidf_matrix[hist_cbf]
    cand_vecs = cbf_model.tfidf_matrix[cand_valid]
    sims = cosine_similarity(hist_vecs, cand_vecs).max(axis=0)

    full_scores = np.zeros(len(candidates))
    vi = 0
    for ci, v in enumerate(valid_mask):
        if v:
            full_scores[ci] = sims[vi]
            vi += 1

    pos_score  = full_scores[label_idx]
    neg_scores = np.delete(full_scores, label_idx)

    pos_scores_all.append(pos_score)
    neg_scores_all.extend(neg_scores.tolist())
    if pos_score >= np.max(neg_scores):
        pos_beat_neg += 1
    total_valid += 1

pos_arr = np.array(pos_scores_all)
neg_arr = np.array(neg_scores_all)
print(f"  Avg similarity POSITIF           : {pos_arr.mean():.4f}  (std: {pos_arr.std():.4f})")
print(f"  Avg similarity NEGATIF           : {neg_arr.mean():.4f}  (std: {neg_arr.std():.4f})")
print(f"  Gap (pos_mean - neg_mean)        : {pos_arr.mean() - neg_arr.mean():.4f}")
print(f"  % positif mengalahkan semua neg  : {pos_beat_neg/total_valid*100:.1f}%")
print(f"  AUC proxy P(pos>neg)             : {np.mean(pos_arr > neg_arr[:len(pos_arr)]):.4f}")

# =========================================================================
# H3: History length vs HR@10
# =========================================================================
print("\n" + SEP)
print("H3: Panjang history user vs HR@10")
print(SEP)

buckets = {"1-3": [], "4-10": [], "11-30": [], ">30": []}
for entry in loo_data[:2000]:
    u = entry["u"]
    pos_item = entry["pos_item"]
    candidates = entry["candidates"]
    label_idx  = entry["label_idx"]

    if pos_item not in idx2cbf:
        continue
    hist_cbf = [idx2cbf[i] for i in user_history.get(u, []) if i in idx2cbf]
    if not hist_cbf:
        continue
    n_hist = len(hist_cbf)

    cand_cbf   = [idx2cbf.get(c) for c in candidates]
    valid_mask = [i is not None for i in cand_cbf]
    cand_valid = [i for i in cand_cbf if i is not None]
    if not cand_valid:
        continue

    hist_vecs = cbf_model.tfidf_matrix[hist_cbf]
    cand_vecs = cbf_model.tfidf_matrix[cand_valid]
    sims = cosine_similarity(hist_vecs, cand_vecs).max(axis=0)

    full_scores = np.zeros(len(candidates))
    vi = 0
    for ci, v in enumerate(valid_mask):
        if v:
            full_scores[ci] = sims[vi]
            vi += 1

    ranked = np.argsort(full_scores)[::-1].tolist()
    hit10 = 1.0 if label_idx in ranked[:10] else 0.0

    if n_hist <= 3:
        buckets["1-3"].append(hit10)
    elif n_hist <= 10:
        buckets["4-10"].append(hit10)
    elif n_hist <= 30:
        buckets["11-30"].append(hit10)
    else:
        buckets[">30"].append(hit10)

for label, hits in buckets.items():
    if hits:
        print(f"  History {label:>5} item : HR@10 = {np.mean(hits):.4f}  (n={len(hits):,})")

# =========================================================================
# H4: Sparsity bahan -- cosine similarity antar pasangan resep acak
# =========================================================================
print("\n" + SEP)
print("H4: Sparsity bahan -- cosine similarity antar 300 resep acak")
print(SEP)

sample_idx = np.random.default_rng(42).choice(cbf_model.tfidf_matrix.shape[0], 300, replace=False)
sample_mat = cbf_model.tfidf_matrix[sample_idx]
sim_matrix = cosine_similarity(sample_mat)
np.fill_diagonal(sim_matrix, 0)
flat_sims = sim_matrix.flatten()

print(f"  Rata-rata cosine sim antar resep    : {flat_sims.mean():.4f}")
print(f"  Median cosine sim antar resep       : {np.median(flat_sims):.4f}")
print(f"  % pasangan dengan sim = 0           : {np.mean(flat_sims == 0)*100:.1f}%")
print(f"  % pasangan dengan sim < 0.1         : {np.mean(flat_sims < 0.1)*100:.1f}%")
print(f"  % pasangan dengan sim > 0.3         : {np.mean(flat_sims > 0.3)*100:.1f}%")

nnz_per_row = np.diff(sample_mat.indptr)
print(f"\n  Rata-rata token non-zero per resep  : {nnz_per_row.mean():.1f}")
print(f"  Median token non-zero               : {np.median(nnz_per_row):.1f}")
print(f"  Min / Max token non-zero            : {nnz_per_row.min()} / {nnz_per_row.max()}")

print("\n" + SEP2)
print("  Selesai. Lihat angka di atas untuk kesimpulan diagnosis.")
print(SEP2)
