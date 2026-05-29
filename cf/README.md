# Collaborative Filtering for Food.com Recipe Recommendation

Modul ini mengimplementasikan sistem rekomendasi resep makanan menggunakan pendekatan **Collaborative Filtering (CF)** dengan model berbasis implicit feedback. Modul ini bertugas sebagai tahap pertama (*Candidate Generation*) dalam arsitektur sistem rekomendasi hibrida yang direncanakan.

## 1. Latar Belakang & Motivasi

Dataset asli Food.com menyediakan interaksi antara pengguna (user) dan resep (item) yang mencakup rating (0-5) dan ulasan teks. Untuk tugas *Collaborative Filtering*, kita memformulasikan masalah ini sebagai **Implicit Feedback Recommendation**. 
- Semua rating positif (> 0) diperlakukan sebagai sinyal positif (1).
- Rating 0 diperlakukan sebagai "unobserved" karena maknanya ambigu (bisa berarti tidak suka, atau belum pernah mencoba).

### Masalah pada Data Split Bawaan (Dataset Paper Asli)
Dataset awal (`interactions_train.csv`, `interactions_test.csv`) tidak didesain untuk tugas CF, melainkan untuk tugas *recipe generation*. Data test memisahkan resep berdasarkan waktu rilisnya, sehingga **100% resep di set pengujian tidak pernah muncul di set pelatihan**. 
Hal ini mengakibatkan model CF—yang sangat bergantung pada matriks interaksi yang diketahui—mengalami *cold-start* ekstrem pada item, sehingga metrik performa mendekati nol (setara tebakan acak).

## 2. Metodologi Data (The Fix)

Untuk melatih dan mengevaluasi model CF dengan tepat, dilakukan pembuatan ulang skema pembagian data (*data split*) secara langsung dari `RAW_interactions.csv` (`01_build_cf_split.ipynb`).

1. **Penyaringan (Co-filtering)**:
   - Pengguna dengan **kurang dari 5 interaksi** dihapus.
   - Resep dengan **kurang dari 3 interaksi** dihapus.
   - Proses ini dilakukan secara iteratif hingga konvergen untuk mengurangi *sparsity* berlebihan.
2. **Pembagian Temporal Leave-One-Out (LOO)**:
   - Data diurutkan berdasarkan waktu per pengguna.
   - **Test Set**: Interaksi paling terakhir dari setiap pengguna.
   - **Validation Set**: Interaksi kedua terakhir dari setiap pengguna.
   - **Train Set**: Sisa riwayat interaksi pengguna sebelumnya.

Melalui desain ini, 99.8% resep yang muncul di Validation/Test set sudah dipelajari (*observed*) di Train set.

## 3. Algoritma Model

Modul ini mengevaluasi beberapa algoritma Matrix Factorization dan Neural Network unggulan untuk data *implicit feedback*:
1. **Alternating Least Squares (ALS)**: Meminimalkan *confidence-weighted squared error*.
2. **Bayesian Personalized Ranking (BPR)**: Menggunakan pendekatan *pairwise ranking*. 
3. **Singular Value Decomposition (SVD)**: MF klasik dengan injeksi sampel negatif (via `scikit-surprise`).
4. **Neural Collaborative Filtering (NCF)**: Arsitektur *Deep Learning* (GMF + MLP) menggunakan PyTorch.

## 4. Evaluasi & Metrik

Pengujian dilakukan menggunakan protokol standar Leave-One-Out:
- **Kandidat Test**: 1 item positif (ground truth) dicampur dengan 99 item negatif (sampel acak yang tidak ada di riwayat pengguna).
- **Metrik Utama**: Hit Rate pada K (HR@5, HR@10, HR@20) dan Mean Reciprocal Rank (MRR).

## 5. Hasil Eksperimen (Final Comparison)

Berikut adalah perbandingan performa antar model setelah dilakukan *hyperparameter tuning* (quick grid search):

### Ringkasan Performa di Test Set

| Model | HR@5 | HR@10 | HR@20 | MRR |
| :--- | :---: | :---: | :---: | :---: |
| **NCF** ⭐ | **0.4172** | **0.5201** | **0.6303** | **0.3095** |
| **SVD** | 0.4096 | 0.5140 | 0.6184 | 0.2996 |
| ALS | 0.3849 | 0.4654 | 0.5602 | 0.2951 |
| BPR | 0.2555 | 0.3643 | 0.5064 | 0.1905 |

### Analisis Hasil
1. **Keunggulan NCF**: NCF memberikan hasil tertinggi di semua metrik, membuktikan efektivitas Deep Learning dalam menangkap interaksi kompleks antara pengguna dan resep.
2. **SVD yang Stabil**: SVD menunjukkan performa yang sangat kompetitif dan hampir menyamai NCF, memperlihatkan bahwa MF klasik tetap kuat jika ditangani dengan sampel negatif yang tepat.
3. **Threshold Performa**: Hasil HR@10 di atas 0.5 menunjukkan sistem berhasil menempatkan resep yang benar-benar disukai pengguna dalam daftar 10 rekomendasi teratas pada lebih dari 50% kasus pengujian.

Model terbaik (**NCF**) dipilih sebagai komponen utama tahap *candidate generation* untuk sistem *Hybrid Recommendation*.

## 6. Struktur Kode & Penggunaan

- `cf/01_build_cf_split.ipynb`: Notebook pembuatan data split LOO.
- `cf/02_train_evaluate_cf.ipynb`: Notebook eksperimen training & evaluasi model.
- `cf/data_prep.py`: Utilitas pemrosesan matriks dan data.
- `cf/evaluator.py`: Metrik evaluasi (HR, MRR).
- `cf/models/`: Folder berisi implementasi modular `ALSModel`, `BPRModel`, `SVDModel`, dan `NCFModel`.
- `cf/outputs/`: Folder berisi hasil split data, CSV metrik, dan model terbaik yang disimpan.
