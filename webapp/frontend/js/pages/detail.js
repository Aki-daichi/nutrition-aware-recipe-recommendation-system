import { api } from '../api.js?v=2.0.0';
import { state } from '../state.js?v=2.0.0';
import { showToast, observeFadeIn } from '../ui.js?v=2.0.0';
import { getNavbarHtml, attachNavbarListeners } from './dashboard.js?v=2.0.0';

let selectedRating = 0;

export const DetailPage = {
  async render(container, params) {
    const recipeId = parseInt(params.id, 10);
    const user = state.currentUser;
    
    if (!user) {
      window.location.hash = '#/login';
      return;
    }

    container.innerHTML = `
      ${getNavbarHtml()}
      
      <main class="detail-content">
        <!-- Breadcrumbs & Back Button -->
        <div class="detail-breadcrumbs">
          <a href="#/" class="detail-back-link">
            <i class="ph-bold ph-arrow-left"></i> Kembali ke Beranda
          </a>
          <span class="detail-breadcrumb-separator">&middot;</span>
          <span class="detail-breadcrumb-title" id="recipe-breadcrumb">Resep</span>
        </div>

        <div id="recipe-detail-loading" class="detail-loading">
          <i class="ph-bold ph-spinner spinner"></i>
          <p>Memuat detail resep...</p>
        </div>

        <div id="recipe-detail-container" style="display: none;">
          <!-- Detail content loaded dynamically -->
        </div>
      </main>
    `;

    attachNavbarListeners(container);

    const loadingDiv = container.querySelector('#recipe-detail-loading');
    const detailDiv = container.querySelector('#recipe-detail-container');

    try {
      const recipe = await api.getRecipeDetail(recipeId);
      selectedRating = 0;

      const cleanName = recipe.name.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
      
      // Update breadcrumb
      container.querySelector('#recipe-breadcrumb').textContent = cleanName;

      // Build tags
      const tagsHtml = recipe.tags.slice(0, 10).map(tag => `
        <span class="badge detail-tag-badge">
          ${tag}
        </span>
      `).join(' ');

      // Nutrition details
      const nutDetails = recipe.nutrition;
      const nutritionDetails = [
        { name: 'Kalori', value: Math.round(nutDetails.calories), unit: 'kkal', max: 2000, desc: 'Energi dasar harian' },
        { name: 'Lemak Total', value: Math.round(nutDetails.total_fat_pdv), unit: '% DV', max: 100, desc: 'Lemak harian direkomendasikan' },
        { name: 'Gula', value: Math.round(nutDetails.sugar_pdv), unit: '% DV', max: 100, desc: 'Kandungan gula tambahan' },
        { name: 'Sodium', value: Math.round(nutDetails.sodium_pdv), unit: '% DV', max: 100, desc: 'Asupan garam (Sodium)' },
        { name: 'Protein', value: Math.round(nutDetails.protein_pdv), unit: '% DV', max: 100, desc: 'Protein pembangun otot' },
        { name: 'Lemak Jenuh', value: Math.round(nutDetails.saturated_fat_pdv), unit: '% DV', max: 100, desc: 'Lemak jenuh harian' },
        { name: 'Karbohidrat', value: Math.round(nutDetails.carbs_pdv), unit: '% DV', max: 100, desc: 'Karbohidrat harian' }
      ];

      const nutritionListHtml = nutritionDetails.map((nut) => {
        let colorClass = 'fill-high';
        if (nut.name === 'Gula' || nut.name === 'Sodium' || nut.name === 'Lemak Jenuh') {
          if (nut.value > 50) colorClass = 'fill-low';
          else if (nut.value > 25) colorClass = 'fill-medium';
        } else if (nut.name === 'Protein') {
          if (nut.value > 30) colorClass = 'fill-high';
          else if (nut.value > 15) colorClass = 'fill-medium';
          else colorClass = 'fill-low';
        } else {
          if (nut.value > 75) colorClass = 'fill-low';
          else if (nut.value > 40) colorClass = 'fill-medium';
        }

        return `
          <div class="nutrition-item-row">
            <div class="nutrition-item-label-row">
              <span><strong>${nut.name}</strong> <span class="nutrition-item-desc">(${nut.desc})</span></span>
              <span class="nutrition-item-val">${nut.value} ${nut.unit}</span>
            </div>
            <div class="nutrition-track thin-track">
              <div class="nutrition-fill ${colorClass}" style="width: ${Math.min(nut.value, 100)}%"></div>
            </div>
          </div>
        `;
      }).join('');

      const recInfo = state.recommendations.find(r => r.recipe_id === recipeId);
      let scoreWidgetHtml = '';
      if (recInfo) {
        scoreWidgetHtml = `
          <div class="card score-widget-card">
            <h4 class="score-widget-title">Analisis Skor Rekomendasi</h4>
            <div class="analysis-stats-grid">
              <div class="analysis-stat-block border-right">
                <div class="analysis-stat-val">${recInfo.cf_score.toFixed(2)}</div>
                <div class="analysis-stat-label">CF Score</div>
              </div>
              <div class="analysis-stat-block border-right">
                <div class="analysis-stat-val">${recInfo.similarity_score.toFixed(2)}</div>
                <div class="analysis-stat-label">CBF Score</div>
              </div>
              <div class="analysis-stat-block">
                <div class="analysis-stat-val green">${recInfo.nutrition_score.toFixed(1)}</div>
                <div class="analysis-stat-label">Gizi</div>
              </div>
            </div>
            <hr class="score-widget-divider">
            <div class="score-widget-row">
              <span>Sinyal Dominan:</span>
              <strong class="score-widget-val">${recInfo.dominant_signal === 'CF' ? 'Minat Pengguna (CF)' : recInfo.dominant_signal === 'CBF' ? 'Kemiripan Bahan (CBF)' : 'Nilai Gizi (Nutrition)'}</strong>
            </div>
            <div class="score-widget-row highlight">
              <span><strong>Skor Akhir:</strong></span>
              <strong class="score-widget-final-val">${recInfo.final_score.toFixed(4)}</strong>
            </div>
          </div>
        `;
      }

      const ingredientsHtml = recipe.ingredients.map(ing => `
        <li class="ingredient-item">
          <input type="checkbox" class="ingredient-checkbox">
          <span class="ingredient-text" onclick="const cb = this.previousElementSibling; cb.checked = !cb.checked;">${ing}</span>
        </li>
      `).join('');

      const stepsHtml = recipe.steps.map((step, idx) => `
        <div class="step-item">
          <div class="step-number">
            ${idx + 1}
          </div>
          <p class="step-text">${step}</p>
        </div>
      `).join('');

      detailDiv.innerHTML = `
        <div class="recipe-detail-header-block">
          <h2 class="recipe-detail-title">${cleanName}</h2>
          <p class="recipe-detail-desc">
            ${recipe.description || 'Tidak ada deskripsi untuk resep ini.'}
          </p>
          <div class="recipe-detail-tags">
            ${tagsHtml}
          </div>
        </div>

        <div class="recipe-stats-grid">
          <div class="card stat-card">
            <div class="stat-card-label">Waktu</div>
            <strong class="stat-card-val">${recipe.minutes} Menit</strong>
          </div>
          <div class="card stat-card">
            <div class="stat-card-label">Total Bahan</div>
            <strong class="stat-card-val">${recipe.n_ingredients} Bahan</strong>
          </div>
          <div class="card stat-card">
            <div class="stat-card-label">Kalori</div>
            <strong class="stat-card-val">${Math.round(nutDetails.calories)} kkal</strong>
          </div>
        </div>

        <div class="recipe-detail-grid">
          <!-- Left Column: Nutrition & Ingredients -->
          <div>
            ${scoreWidgetHtml}

            <div class="recipe-detail-section">
              <h3 class="section-heading">Profil Gizi</h3>
              <div class="card nutrition-profile-card">
                ${nutritionListHtml}
              </div>
            </div>

            <div class="recipe-detail-section">
              <h3 class="section-heading">Bahan-bahan</h3>
              <div class="card ingredients-card">
                <ul class="ingredients-list">
                  ${ingredientsHtml}
                </ul>
              </div>
            </div>
          </div>

          <!-- Right Column: Cooking Steps & Rating -->
          <div>
            <div class="recipe-detail-section">
              <h3 class="section-heading">Instruksi Memasak</h3>
              <div class="card steps-card">
                ${stepsHtml}
              </div>
            </div>

            <div class="card rating-card">
              <h3 class="rating-card-title">Beri Ulasan Resep Ini</h3>
              <p class="rating-card-subtitle">
                Berikan rating untuk memperbarui model Collaborative Filtering personalisasi Anda secara dinamis.
              </p>
              
              <div class="rating-card-footer">
                <div class="rating-stars" id="star-rating-widget">
                  <i class="ph-fill ph-star" data-value="1"></i>
                  <i class="ph-fill ph-star" data-value="2"></i>
                  <i class="ph-fill ph-star" data-value="3"></i>
                  <i class="ph-fill ph-star" data-value="4"></i>
                  <i class="ph-fill ph-star" data-value="5"></i>
                </div>
                <button type="button" class="btn btn-primary rating-submit-btn" id="btn-submit-rating" disabled>Kirim Rating</button>
              </div>
            </div>
          </div>
        </div>
      `;

      const stars = detailDiv.querySelectorAll('#star-rating-widget i');
      const submitBtn = detailDiv.querySelector('#btn-submit-rating');
      
      stars.forEach(star => {
        star.addEventListener('click', () => {
          const val = parseInt(star.dataset.value, 10);
          selectedRating = val;
          
          stars.forEach((s, i) => {
            if (i < val) {
              s.classList.add('active');
            } else {
              s.classList.remove('active');
            }
          });
          
          submitBtn.removeAttribute('disabled');
        });
      });

      submitBtn.addEventListener('click', async () => {
        if (!selectedRating) return;
        
        submitBtn.setAttribute('disabled', 'true');
        submitBtn.innerHTML = '<i class="ph-bold ph-spinner spinner" style="margin-right: 6px;"></i> Mengirim...';

        try {
          await api.postInteraction(user.user_id, recipeId, selectedRating);
          showToast(`Terima kasih! Ulasan ${selectedRating} bintang berhasil disimpan.`, 'success');
          
          selectedRating = 0;
          stars.forEach(s => s.classList.remove('active'));
          submitBtn.textContent = 'Kirim Rating';
        } catch (err) {
          showToast(`Gagal menyimpan rating: ${err.message}`, 'error');
          submitBtn.removeAttribute('disabled');
          submitBtn.textContent = 'Kirim Rating';
        }
      });

      loadingDiv.style.display = 'none';
      detailDiv.style.display = 'block';

      observeFadeIn(detailDiv);

    } catch (err) {
      console.error('Failed to load recipe detail:', err);
      loadingDiv.innerHTML = `
        <i class="ph-bold ph-warning-circle" style="font-size: 32px; color: var(--pale-red-text); margin-bottom: 12px;"></i>
        <p>Gagal memuat detail resep: ${err.message}</p>
      `;
    }
  }
};
