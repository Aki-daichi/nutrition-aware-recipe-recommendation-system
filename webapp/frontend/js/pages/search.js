import { api } from '../api.js?v=2.0.0';
import { state } from '../state.js?v=2.0.0';
import { getNutritionBarHtml, animateStagger } from '../ui.js?v=2.0.0';
import { getNavbarHtml, attachNavbarListeners } from './dashboard.js?v=2.0.0';

export const SearchPage = {
  async render(container, params, queryParams) {
    const user = state.currentUser;
    if (!user) {
      window.location.hash = '#/login';
      return;
    }

    const searchQuery = queryParams.q || '';

    container.innerHTML = `
      ${getNavbarHtml()}
      
      <main class="search-content">
        <div class="search-header-block">
          <h2 class="search-title">Hasil Pencarian</h2>
          <p class="search-subtitle">
            Menampilkan resep sehat untuk kata kunci: <strong class="search-query-highlight">"${searchQuery}"</strong>
          </p>
        </div>

        <div id="search-loading" class="search-loading">
          <i class="ph-bold ph-spinner spinner"></i>
          <p>Mencari resep...</p>
        </div>

        <div id="search-results-grid" class="recommendation-grid" style="display: none;">
          <!-- Search results render here -->
        </div>

        <div id="search-empty" class="search-empty" style="display: none;">
          <i class="ph-bold ph-magnifying-glass"></i>
          <p>Tidak ditemukan resep sehat yang cocok dengan kata kunci "${searchQuery}".</p>
          <a href="#/" class="btn btn-secondary">Kembali ke Beranda</a>
        </div>
      </main>
    `;

    attachNavbarListeners(container);

    const navSearchInput = container.querySelector('#nav-search-input');
    if (navSearchInput) {
      navSearchInput.value = searchQuery;
    }

    const loadingDiv = container.querySelector('#search-loading');
    const gridDiv = container.querySelector('#search-results-grid');
    const emptyDiv = container.querySelector('#search-empty');

    try {
      const results = await api.searchRecipes(searchQuery, '', 40, 0);

      loadingDiv.style.display = 'none';

      if (!results || results.length === 0) {
        emptyDiv.style.display = 'block';
        return;
      }

      gridDiv.innerHTML = results.map(r => renderSearchRecipeCard(r)).join('');
      gridDiv.style.display = 'grid';

      animateStagger('#search-results-grid', '.recipe-card');

    } catch (err) {
      console.error('Failed to run search:', err);
      loadingDiv.innerHTML = `
        <i class="ph-bold ph-warning-circle" style="font-size: 32px; color: var(--pale-red-text); margin-bottom: 12px;"></i>
        <p>Gagal memproses pencarian: ${err.message}</p>
      `;
    }

    function renderSearchRecipeCard(recipe) {
      const calories = recipe.calories !== undefined ? recipe.calories : 0;
      const score = recipe.nutrition_score !== undefined ? recipe.nutrition_score : 50.0;
      
      return `
        <div class="recipe-card" data-id="${recipe.recipe_id || recipe.id}">
          <div class="recipe-card-img-placeholder">
            <img src="assets/food_placeholder.png" alt="${recipe.name}" class="recipe-card-img">
          </div>
          <div class="recipe-card-body">
            <h4 class="recipe-card-title">${recipe.name}</h4>
            <div class="recipe-card-meta">
              <span>${recipe.minutes} Mnt</span>
              <span>&middot;</span>
              <span>${recipe.n_ingredients} Bahan</span>
              <span>&middot;</span>
              <span>${Math.round(calories)} kkal</span>
            </div>
            <div class="recipe-card-score-container">
              <div class="recipe-card-score-row">
                <span>Kesehatan</span>
                <span class="recipe-card-score-val">${Math.round(score)}</span>
              </div>
              ${getNutritionBarHtml(score)}
            </div>
          </div>
        </div>
      `;
    }

    container.addEventListener('click', (e) => {
      const card = e.target.closest('.recipe-card');
      if (card) {
        const id = card.getAttribute('data-id');
        window.location.hash = `#/recipe/${id}`;
      }
    });
  }
};
