# 🥗 Nutrition-Aware Recipe Recommendation System

> **Capstone Project — PJK-GM053 | Pijak × IBM SkillsBuild | Tema 3**

Sistem rekomendasi resep makanan berbasis pendekatan **Weighted Hybrid** yang menggabungkan *Neural Collaborative Filtering* (preferensi pengguna), *Content-Based Filtering* TF-IDF (kesamaan bahan & tag), dan *Nutrition Scoring* (aspek kesehatan) secara bersamaan.

---

## 👥 Tim

| ID | Nama | Peran |
|:---|:-----|:------|
| APC126D6Y0548 | Amr Fadhilah Abiyyu Alif Basysyar | Project Lead + ML Engineer (CF) |
| APC126D6Y0547 | Thafa Fadillah Ramdani | Data Engineer + Preprocessing |
| APC126D6Y0484 | Micho Dhani Firmansyah | ML Engineer (CBF) + Nutrition Logic |
| APC126D6Y0551 | Dzaka Fadhlillah Hakim | Full-stack Demo + Evaluation |

---

## 📌 Latar Belakang & Problem Statement

Platform kuliner digital umumnya merekomendasikan resep berdasarkan popularitas semata, tanpa mempertimbangkan preferensi personal atau profil nutrisi pengguna. Proyek ini membangun sistem rekomendasi yang mampu **menyeimbangkan relevansi selera (*taste accuracy*) dan kualitas kesehatan (*nutritional awareness*)** secara bersamaan.

**Research Question:**
> Seberapa efektif sistem rekomendasi *Weighted Hybrid* (menggabungkan NCF, TF-IDF, dan Nutrition Scoring) dalam menyeimbangkan *trade-off* antara akurasi rekomendasi (Hit Rate@K dan MRR) dan kualitas nutrisi dibandingkan model baseline tunggal?

---

## 🏗️ Arsitektur Sistem

Pipeline rekomendasi berjalan dalam 4 tahap untuk setiap pengguna:

```
[Kandidat Resep DB]
       │
       ▼
[Stage 0] Pre-filter → Filter kalori & skor nutrisi minimum (opsional, user-defined)
       │
       ▼
[Stage 1] Collaborative Filtering (NCF) → Skor top-200 kandidat berdasarkan pola interaksi
       │
       ▼
[Stage 2] CBF (TF-IDF) + Nutrition Scoring → Skor kemiripan bahan & tag, skor kesehatan
       │
       ▼
[Stage 3] Weighted Blending → final_score = 0.6·CF + 0.3·CBF + 0.1·Nutrisi → Top-N
```

**Cold-start users** (pengguna baru yang tidak ada dalam model CF) mendapat fallback berupa resep paling populer yang diurutkan berdasarkan skor nutrisi.

---

## 📊 Hasil Evaluasi Model

Evaluasi dilakukan dengan protokol **Leave-One-Out (LOO)** — 1 item positif vs. 99 item negatif per pengguna.

### Model Terbaik — Rumpun Collaborative Filtering

| Model | HR@5 | HR@10 | HR@20 | MRR |
|:------|:----:|:-----:|:-----:|:---:|
| **NCF** ⭐ | **0.4172** | **0.5201** | **0.6303** | **0.3095** |
| SVD | 0.4096 | 0.5140 | 0.6184 | 0.2996 |
| ALS | 0.3849 | 0.4654 | 0.5602 | 0.2951 |
| BPR | 0.2555 | 0.3643 | 0.5064 | 0.1905 |

### Model Terbaik — Rumpun Content-Based Filtering

| Model | HR@5 | HR@10 | HR@20 | MRR |
|:------|:----:|:-----:|:-----:|:---:|
| **TF-IDF** ⭐ | **0.1431** | **0.2312** | **0.3742** | **0.1137** |
| Jaccard | 0.1324 | 0.2213 | 0.3598 | 0.1058 |
| Node2Vec | 0.1152 | 0.2025 | 0.3453 | 0.0954 |
| Word2Vec | 0.1139 | 0.1958 | 0.3308 | 0.0929 |

### Hasil Ablasi — Sistem Hybrid

| Konfigurasi | HR@10 | MRR | Avg_Nutrition |
|:------------|:-----:|:---:|:-------------:|
| Pure CF (NCF) Baseline | 0.5201 | 0.3095 | 15.00 |
| Pure CBF (TF-IDF) Baseline | 0.2312 | 0.1137 | 17.84 |
| Cascade CF→CBF (sequential) | 0.2909 | 0.1297 | 16.73 |
| Cascade + Nutrition Filter (hard) | 0.1208 | 0.0671 | 29.90 |
| **Hybrid (cf=0.7, cbf=0.3, nutr=0.0)** | **0.5378** | **0.3191** | 15.41 |
| **Hybrid (cf=0.6, cbf=0.3, nutr=0.1) ✅** | **0.5008** | **0.3062** | **38.82** |
| Hybrid (cf=0.6, cbf=0.2, nutr=0.2) | 0.4308 | 0.2718 | 58.19 |

**Konfigurasi terpilih:** `cf=0.6, cbf=0.3, nutr=0.1` — akurasi hanya turun 1.9% dari baseline NCF murni, namun kualitas nutrisi rekomendasi meningkat **258.8%**.

---

## 🗂️ Struktur Repositori

```
nutrition-aware-recipe-recommendation-system/
│
├── EDA/                         # Exploratory Data Analysis
│   ├── EDA-Recipe.ipynb         # Analisis dataset resep
│   ├── EDA-Interaction.ipynb    # Analisis pola interaksi pengguna
│   └── parse_picke.ipynb        # Parsing ingr_map.pkl (ingredient tokens)
│
├── dataset/                     # Dataset mentah (tidak di-commit ke Git)
│   ├── RAW_recipes.csv
│   ├── RAW_recipes_cleaned.csv
│   └── ingr_map.pkl
│
├── cf/                          # Modul Collaborative Filtering
│   ├── 01_build_cf_split.ipynb  # Membuat LOO split kustom dari RAW_interactions
│   ├── 02_train_evaluate_cf.ipynb
│   ├── data_prep.py             # Utilitas matriks & LOO evaluation data
│   ├── evaluator.py             # Metrik HR@K dan MRR
│   ├── models/                  # Implementasi ALS, BPR, SVD, NCF
│   └── outputs/                 # Model .pkl, split data, hasil CSV
│
├── cbf/                         # Modul Content-Based Filtering
│   ├── 03_build_cbf.ipynb
│   ├── 04_train_evaluate_cbf.ipynb
│   ├── 04b_train_evaluate_cbf_alternatives.ipynb
│   ├── feature_extractor.py     # TF-IDF text feature extraction
│   ├── nutrition_extractor.py   # Ekstraksi fitur nutrisi resep
│   ├── models/                  # Implementasi TF-IDF, Jaccard, Word2Vec, Node2Vec
│   └── outputs/                 # Model .pkl dan hasil CSV
│
├── nutrition/
│   └── scoring.py               # NutritionScorer & NutritionFilter (0–100 score)
│
├── ablation/                    # Ablation study & integrasi hybrid
│   ├── cascade.py               # Implementasi cascade pipeline
│   ├── run_ablation.py          # Runner eksperimen multi-konfigurasi
│   ├── visualize_pareto.py      # Visualisasi Pareto frontier akurasi vs nutrisi
│   ├── diagnose_cbf.py          # Diagnosis performa CBF
│   ├── hasil_dan_pembahasan.md  # Laporan hasil evaluasi lengkap
│   └── outputs/results/         # Plot & CSV hasil ablasi
│
└── webapp/                      # Prototipe Web Dashboard
    ├── docker-compose.yml       # Orchestration: db + api + frontend
    ├── backend/
    │   ├── main.py              # FastAPI app entry point
    │   ├── settings.py          # Konfigurasi env (DATABASE_URL, model paths)
    │   ├── database.py          # asyncpg connection pool
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── routers/             # Endpoint: auth, users, recipes, recommend, stats
    │   ├── pipeline/            # Inference: CF, CBF, Nutrition, Hybrid blending
    │   ├── schemas/             # Pydantic request/response models
    │   └── scripts/
    │       ├── schema.sql       # Definisi tabel PostgreSQL
    │       └── seed.py          # Script seeding data ke database
    └── frontend/
        ├── index.html
        ├── css/                 # Design system (tokens, base, layout, components)
        └── js/
            ├── api.js           # HTTP client ke backend
            ├── router.js        # Hash-based SPA router
            ├── state.js         # Global state management
            └── pages/           # Login, Dashboard, Search, Detail
```

---

## 🚀 Cara Menjalankan Web App (Docker)

### Prasyarat
- Docker & Docker Compose terinstal
- Dataset Food.com (`RAW_recipes.csv`, `RAW_interactions.csv`) tersedia
- Model terlatih tersedia di `cf/outputs/models/` dan `cbf/outputs/models/`

### 1. Konfigurasi Environment

```bash
# Salin file env contoh
cp webapp/.env.example webapp/.env
```

### 2. Jalankan Docker Compose

```bash
cd webapp
docker compose up --build
```

Ini akan menjalankan 3 service sekaligus:
| Service | Container | Port |
|:--------|:----------|:-----|
| PostgreSQL | `webapp_db` | `5433` |
| FastAPI Backend | `webapp_api` | `8000` |
| Nginx Frontend | `webapp_frontend` | `3000` |

### 3. Seed Database

Jalankan setelah container aktif dan database siap:

```bash
docker exec webapp_api python webapp/backend/scripts/seed.py \
  --data-dir /app/food.com \
  --limit-recipes 20000
```

> Untuk seed semua resep (~230K), gunakan `--limit-recipes 0`. Proses akan lebih lama.

### 4. Akses Aplikasi

- **Dashboard:** [http://localhost:3000](http://localhost:3000)
- **API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

**Login:** Gunakan salah satu ID persona berikut dengan password `nutricook`:

| User ID | Persona | Profil Diet |
|:-------:|:--------|:------------|
| 1533 | Budi Santoso | Fitness Enthusiast (tinggi protein, rendah kalori) |
| 1535 | Siti Aminah | Sugar & Diabetes Prevention (rendah gula) |
| 1581 | Andi Wijaya | Keto Practitioner (padat gizi) |
| 1634 | Dewi Lestari | Weight Loss Journey (kalori sangat ketat) |

---

## 🔬 Menjalankan Pipeline ML (Notebook)

Jalankan notebook secara berurutan:

```
1. EDA/EDA-Recipe.ipynb             → Memahami struktur dataset
2. EDA/EDA-Interaction.ipynb        → Memahami pola interaksi
3. cf/01_build_cf_split.ipynb       → Membuat CF LOO split kustom
4. cf/02_train_evaluate_cf.ipynb    → Training & evaluasi 4 model CF
5. cbf/03_build_cbf.ipynb           → Membangun TF-IDF feature matrix
6. cbf/04_train_evaluate_cbf.ipynb  → Evaluasi model CBF
7. ablation/run_ablation.py         → Eksperimen konfigurasi hybrid
8. ablation/visualize_pareto.py     → Visualisasi Pareto frontier
```

---

## 🛠️ Tech Stack

| Komponen | Teknologi |
|:---------|:----------|
| ML / Data | Python, PyTorch, scikit-learn, pandas, NumPy, SciPy |
| Backend | FastAPI, Uvicorn, asyncpg, Pydantic |
| Database | PostgreSQL 15 |
| Frontend | HTML, Vanilla CSS, Vanilla JavaScript (SPA) |
| Infrastruktur | Docker, Docker Compose, Nginx |

---

## 📄 Dataset

**Food.com Recipes & Interactions** (Kaggle)
- 160.000+ resep dengan metadata bahan, tag, langkah masak, dan informasi nutrisi
- 700.000+ interaksi dari 25.000+ pengguna mencakup 18 tahun

> ⚠️ Dataset tidak disertakan dalam repositori karena ukurannya. Unduh dari [Kaggle](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions) dan letakkan file `RAW_recipes.csv` dan `RAW_interactions.csv` di folder `food.com/` dan `dataset/`.

---

## 📚 Referensi

1. He, X., et al. (2017). **Neural Collaborative Filtering**. *WWW '17*. https://doi.org/10.1145/3038912.3052569
2. Tamm, Y.-M., et al. (2021). **Quality Metrics in Recommender Systems: Do We Calculate Metrics Consistently?** *RecSys '21*. https://doi.org/10.1145/3460231.3478848

---

## 📝 Lisensi

MIT License — lihat file [LICENSE](LICENSE) untuk detail.
