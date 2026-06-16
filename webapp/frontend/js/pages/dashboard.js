import { api } from '../api.js?v=2.0.0';
import { state } from '../state.js?v=2.0.0';
import { getNutritionBarHtml, getSignalBadgeHtml, animateStagger } from '../ui.js?v=2.0.0';

export function getNavbarHtml() {
  const user = state.currentUser;
  return `
    <header class="app-header">
      <div class="logo-section" onclick="window.location.hash = '#/'">
        <i class="ph-fill ph-bowl-food"></i>
        <h1>NutriCook</h1>
      </div>
      
      <div class="search-section">
        <form id="nav-search-form" class="nav-search-form">
          <input type="text" id="nav-search-input" class="nav-search-input" placeholder="Cari resep sehat..." required>
          <button type="submit" class="nav-search-btn">
            <i class="ph-bold ph-magnifying-glass"></i>
          </button>
        </form>
      </div>
      
      <div class="user-section nav-user-section">
        <div class="user-profile nav-user-profile">
          <div class="avatar-small nav-avatar-small">
            ${user ? user.display_name.charAt(0).toUpperCase() : 'U'}
          </div>
          <span class="nav-username">
            ${user ? user.display_name.split(' (')[0] : 'User'}
          </span>
        </div>
        <button class="btn btn-secondary nav-logout-btn" id="btn-logout" title="Logout">
          <i class="ph-bold ph-sign-out"></i>
          <span class="logout-text">Logout</span>
        </button>
      </div>
    </header>
  `;
}

export function attachNavbarListeners(container) {
  const logoutBtn = container.querySelector('#btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      state.currentUser = null;
      window.location.hash = '#/login';
    });
  }

  const searchForm = container.querySelector('#nav-search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const query = container.querySelector('#nav-search-input').value.trim();
      if (query) {
        window.location.hash = `#/search?q=${encodeURIComponent(query)}`;
      }
    });
  }
}

export const DashboardPage = {
  async render(container) {
    const user = state.currentUser;
    if (!user) {
      window.location.hash = '#/login';
      return;
    }

    container.innerHTML = `
      ${getNavbarHtml()}
      
      <main class="dashboard-content">
        <div class="dashboard-hero">
          <h2>Halo, ${user.display_name}</h2>
          <p class="dashboard-hero-desc">Temukan resep sehat pilihan berdasarkan riwayat dan preferensi nutrisi Anda.</p>
        </div>
        
        <!-- Row 1: Rekomendasi Untukmu -->
        <div class="row-section">
          <div class="row-header">
            <h3>Rekomendasi Untukmu</h3>
            <div class="filter-wrapper">
              <button class="btn btn-secondary" id="btn-filter-toggle">
                <i class="ph-bold ph-sliders-horizontal"></i>
                Filter Nutrisi
              </button>
              
              <!-- Nutrition Filter Overlay -->
              <div class="filter-overlay" id="filter-overlay" style="display: none;">
                <h4>Filter Kandungan Nutrisi</h4>
                
                <div class="form-group">
                  <div class="filter-label-row">
                    <label>Kalori Maksimum</label>
                    <span id="val-calories">1000 kkal</span>
                  </div>
                  <input type="range" id="filter-calories" min="100" max="2000" step="50" value="1000">
                </div>
                
                <div class="form-group">
                  <div class="filter-label-row">
                    <label>Skor Kesehatan Minimum</label>
                    <span id="val-nutrition">60</span>
                  </div>
                  <input type="range" id="filter-nutrition" min="0" max="100" step="5" value="60">
                </div>
                
                <div class="filter-actions-row">
                  <button type="button" class="btn btn-secondary" id="btn-filter-reset">Reset</button>
                  <button type="button" class="btn btn-primary" id="btn-filter-apply">Terapkan</button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="horizontal-scroll" id="recs-scroll">
            <div class="scroll-loading">
              <i class="ph-bold ph-spinner spinner"></i>
              <p>Memuat rekomendasi resep...</p>
            </div>
          </div>
        </div>
        
        <!-- Row 2: Sedang Populer -->
        <div class="row-section">
          <div class="row-header">
            <h3>Sedang Populer</h3>
          </div>
          <div class="horizontal-scroll" id="popular-scroll">
            <div class="scroll-loading">
              <i class="ph-bold ph-spinner spinner"></i>
              <p>Memuat resep populer...</p>
            </div>
          </div>
        </div>
      </main>
    `;

    attachNavbarListeners(container);

    const btnFilterToggle = container.querySelector('#btn-filter-toggle');
    const filterOverlay = container.querySelector('#filter-overlay');
    const sliderCalories = container.querySelector('#filter-calories');
    const valCalories = container.querySelector('#val-calories');
    const sliderNutrition = container.querySelector('#filter-nutrition');
    const valNutrition = container.querySelector('#val-nutrition');
    const btnFilterApply = container.querySelector('#btn-filter-apply');
    const btnFilterReset = container.querySelector('#btn-filter-reset');

    const currentFilters = state.activeFilters;
    if (currentFilters.max_calories) {
      sliderCalories.value = currentFilters.max_calories;
      valCalories.textContent = `${currentFilters.max_calories} kkal`;
    } else {
      sliderCalories.value = 2000;
      valCalories.textContent = 'Tanpa Batas';
    }

    if (currentFilters.min_nutrition_score) {
      sliderNutrition.value = currentFilters.min_nutrition_score;
      valNutrition.textContent = currentFilters.min_nutrition_score;
    } else {
      sliderNutrition.value = 0;
      valNutrition.textContent = 'Tanpa Batas';
    }

    btnFilterToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = filterOverlay.style.display === 'block';
      filterOverlay.style.display = isOpen ? 'none' : 'block';
      if (!isOpen) {
        btnFilterToggle.classList.add('btn-primary');
        btnFilterToggle.classList.remove('btn-secondary');
      } else {
        btnFilterToggle.classList.remove('btn-primary');
        btnFilterToggle.classList.add('btn-secondary');
      }
    });

    document.addEventListener('click', (e) => {
      if (filterOverlay && !filterOverlay.contains(e.target) && e.target !== btnFilterToggle) {
        filterOverlay.style.display = 'none';
        btnFilterToggle.classList.remove('btn-primary');
        btnFilterToggle.classList.add('btn-secondary');
      }
    });

    sliderCalories.addEventListener('input', () => {
      const val = parseInt(sliderCalories.value, 10);
      valCalories.textContent = val === 2000 ? 'Tanpa Batas' : `${val} kkal`;
    });

    sliderNutrition.addEventListener('input', () => {
      const val = parseInt(sliderNutrition.value, 10);
      valNutrition.textContent = val === 0 ? 'Tanpa Batas' : val;
    });

    btnFilterReset.addEventListener('click', () => {
      sliderCalories.value = 2000;
      valCalories.textContent = 'Tanpa Batas';
      sliderNutrition.value = 0;
      valNutrition.textContent = 'Tanpa Batas';
      
      state.resetFilters();
      filterOverlay.style.display = 'none';
      btnFilterToggle.classList.remove('btn-primary');
      btnFilterToggle.classList.add('btn-secondary');
      
      loadRecommendations();
    });

    btnFilterApply.addEventListener('click', () => {
      const maxC = parseInt(sliderCalories.value, 10);
      const minN = parseInt(sliderNutrition.value, 10);
      
      state.activeFilters = {
        max_calories: maxC === 2000 ? null : maxC,
        min_nutrition_score: minN === 0 ? null : minN
      };
      
      filterOverlay.style.display = 'none';
      btnFilterToggle.classList.remove('btn-primary');
      btnFilterToggle.classList.add('btn-secondary');
      
      loadRecommendations();
    });

    async function loadRecommendations() {
      const recsScroll = container.querySelector('#recs-scroll');
      recsScroll.innerHTML = `
        <div class="scroll-loading">
          <i class="ph-bold ph-spinner spinner"></i>
          <p>Menghitung ulang rekomendasi...</p>
        </div>
      `;

      try {
        const filters = state.activeFilters;
        const res = await api.postRecommend(user.user_id, 15, filters);
        state.recommendations = res.recommendations;
        renderRecommendationsList(res.recommendations);
      } catch (err) {
        recsScroll.innerHTML = `
          <div class="scroll-error">
            <i class="ph-bold ph-warning-circle"></i>
            <p>Gagal memuat rekomendasi: ${err.message}</p>
          </div>
        `;
      }
    }

    function renderRecommendationsList(recs) {
      const recsScroll = container.querySelector('#recs-scroll');
      if (!recs || recs.length === 0) {
        recsScroll.innerHTML = `
          <div class="scroll-empty">
            <i class="ph-bold ph-info"></i>
            <p>Tidak ada resep yang cocok dengan filter nutrisi Anda.</p>
          </div>
        `;
        return;
      }

      recsScroll.innerHTML = recs.map(r => renderRecipeCard(r, true)).join('');
      animateStagger('#recs-scroll', '.recipe-card');
    }

    async function loadPopular() {
      const popularScroll = container.querySelector('#popular-scroll');
      try {
        const popular = await api.getPopular(15);
        state.popularRecipes = popular;
        popularScroll.innerHTML = popular.map(r => renderRecipeCard(r, false)).join('');
        animateStagger('#popular-scroll', '.recipe-card');
      } catch (err) {
        popularScroll.innerHTML = `
          <div class="scroll-error">
            <i class="ph-bold ph-warning-circle"></i>
            <p>Gagal memuat resep populer: ${err.message}</p>
          </div>
        `;
      }
    }

    function renderRecipeCard(recipe, isRec = false) {
      const calories = recipe.calories !== undefined ? recipe.calories : 0;
      const score = recipe.nutrition_score !== undefined ? recipe.nutrition_score : 50.0;
      const ratingHtml = recipe.avg_rating !== undefined && recipe.interaction_count > 0 ? `
        <div class="recipe-card-rating">
          <i class="ph-fill ph-star"></i>
          <strong>${recipe.avg_rating.toFixed(1)}</strong>
          <span>(${recipe.interaction_count})</span>
        </div>
      ` : '';
      
      const explanationHtml = isRec && recipe.dominant_signal ? `
        <div class="card-explanation">
          ${getSignalBadgeHtml(recipe.dominant_signal)}
        </div>
      ` : '';

      return `
        <div class="recipe-card" data-id="${recipe.recipe_id || recipe.id}">
          <div class="recipe-card-img-placeholder">
            <img src="assets/food_placeholder.png" alt="${recipe.name}" class="recipe-card-img">
          </div>
          <div class="recipe-card-body">
            ${explanationHtml}
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
            ${ratingHtml}
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

    loadRecommendations();
    loadPopular();
  }
};
