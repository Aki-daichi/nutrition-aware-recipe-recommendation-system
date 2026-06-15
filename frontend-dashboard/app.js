(() => {
  const API_BASE_URL = "http://localhost:8000";

  const $ = (sel) => document.querySelector(sel);

  const els = {
    form: $("#form-recommend"),
    userId: $("#user_id"),
    topN: $("#top_n"),
    topNValue: $("#topn_value"),
    minNutrition: $("#min_nutrition_score"),
    maxCalories: $("#max_calories"),
    refRecipeId: $("#ref_recipe_id"),

    status: $("#status"),
    loading: $("#loading"),
    error: $("#error"),
    cards: $("#cards"),
    empty: $("#empty"),
    resultMeta: $("#result-meta"),

    statTotalRecipes: $("#stat-total-recipes"),
    statTotalUsers: $("#stat-total-users"),
    statTotalInteractions: $("#stat-total-interactions"),
    statSparsity: $("#stat-sparsity"),

    panelDemo: $("#panel-demo"),
    panelEval: $("#panel-eval"),
    tabDemo: $("#tab-demo"),
    tabEval: $("#tab-eval"),
  };

  function setStatus(msg, isError = false) {
    if (!els.status) return;
    els.status.textContent = msg || "";
    els.status.style.color = isError ? "rgba(255,200,200,0.95)" : "";
  }

  function show(el) {
    if (el) el.hidden = false;
  }
  function hide(el) {
    if (el) el.hidden = true;
  }

  function badgeClassForScore(score, type) {
    if (type === "nutrition") {
      if (score >= 75) return "badge--good";
      if (score >= 55) return "badge--mid";
      return "badge--bad";
    }
    if (score >= 0.66) return "badge--good";
    if (score >= 0.4) return "badge--mid";
    return "badge--bad";
  }

  function clamp(n, a, b) {
    return Math.min(b, Math.max(a, n));
  }

  async function safeJson(res) {
    try {
      return await res.json();
    } catch {
      return null;
    }
  }

  async function fetchStats() {
    const url = `${API_BASE_URL}/stats`;
    const res = await fetch(url, { method: "GET" });
    if (!res.ok) throw new Error(`GET /stats failed (${res.status})`);
    return res.json();
  }



  function renderStats(stats) {
    if (!stats) return;
    const fmtInt = (n) => Number(n).toLocaleString();
    els.statTotalRecipes.textContent = fmtInt(stats.total_recipes);
    els.statTotalUsers.textContent = fmtInt(stats.total_users);
    els.statTotalInteractions.textContent = fmtInt(stats.total_interactions);
    els.statSparsity.textContent = `${(stats.sparsity * 100).toFixed(2)}%`;
  }



  function escapeHtml(s) {
    const str = String(s);
    return str
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatNumber(n, digits = 3) {
    if (typeof n !== "number" || Number.isNaN(n)) return String(n);
    return n.toFixed(digits);
  }

  function scoreBadge({ label, value, type }) {
    const cls = badgeClassForScore(value, type);
    return `
      <div class="badge ${cls}">
        <div class="badge__label">${label}</div>
        <div class="badge__value">${type === "nutrition" ? Math.round(value) : formatNumber(value, 3)}</div>
      </div>
    `;
  }

  function whyLabel(dominant_signal) {
    if (dominant_signal === "CF") return "Dominant signal: Collaborative Filtering";
    if (dominant_signal === "CBF") return "Dominant signal: Content-Based Filtering";
    return "Dominant signal: Nutrition scoring";
  }



  function renderCards(recommendations) {
    els.cards.innerHTML = "";

    if (!recommendations || recommendations.length === 0) {
      show(els.empty);
      return;
    }
    hide(els.empty);

    for (const r of recommendations) {
      const cf = scoreBadge({ label: "CF Score", value: r.cf_score, type: "cf" });
      const cbf = scoreBadge({ label: "Similarity", value: r.similarity_score, type: "cbf" });
      const nut = scoreBadge({ label: "Nutrition", value: r.nutrition_score, type: "nutrition" });

      const rankPill = `<div class="rankPill">Rank <b>#${r.rank}</b></div>`;
      const finalScore = `
        <div class="finalScore">
          <div class="finalScore__label">Final score</div>
          <div class="finalScore__value">${formatNumber(r.final_score, 2)}</div>
        </div>
      `;

      const why = `
        <div class="why">${whyLabel(r.dominant_signal)}
          <span class="badgeDominant">${escapeHtml(r.dominant_signal)}</span>
        </div>
      `;

      const tagChips = (r.tags || [])
        .slice(0, 4)
        .map((t) => `<span class="chip">${escapeHtml(t)}</span>`)
        .join("");

      const card = `
        <div class="card">
          <div class="card__top">
            <div>
              <div class="card__title">${escapeHtml(r.name)}</div>
              <div class="card__meta">
                <span>${r.minutes} min</span>
                <span>•</span>
                <span>${r.n_ingredients} ingredients</span>
                <span>•</span>
                <span>${Math.round(r.calories)} kcal</span>
              </div>
              <div class="chips">${tagChips}</div>
            </div>
          </div>

          <div class="scoreRow">
            ${cf}
            ${cbf}
            ${nut}
          </div>

          <div class="card__rank">
            ${rankPill}
            ${finalScore}
          </div>

          ${why}
        </div>
      `;

      els.cards.insertAdjacentHTML("beforeend", card);
    }
  }

  function setActiveTab(which) {
    const isDemo = which === "demo";
    els.tabDemo.classList.toggle("active", isDemo);
    els.tabEval.classList.toggle("active", !isDemo);

    if (els.panelDemo) els.panelDemo.hidden = !isDemo;
    if (els.panelEval) els.panelEval.hidden = isDemo;

    if (els.panelDemo) els.panelDemo.setAttribute("aria-hidden", String(!isDemo));
    if (els.panelEval) els.panelEval.setAttribute("aria-hidden", String(isDemo));
  }

  async function postRecommend(payload) {
    const url = `${API_BASE_URL}/recommend`;
    let res;
    try {
      res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (err) {
      throw new Error("Cannot reach backend. Make sure uvicorn is running on localhost:8000.");
    }

    if (!res.ok) {
      const body = await safeJson(res);
      const msg = body?.detail || body?.message || `HTTP ${res.status}`;
      
      if (res.status === 404) {
        throw new Error("User ID not found in training data. Only 19,123 users from the training dataset are supported.");
      } else if (res.status === 500) {
        throw new Error("Server error. Check the backend terminal for details.");
      } else {
        throw new Error(msg);
      }
    }

    return res.json();
  }

  function renderResultMeta(user_id, top_n) {
    els.resultMeta.textContent = `User #${user_id} • Top-N = ${top_n}`;
  }

  async function onSubmit(e) {
    e.preventDefault();

    hide(els.error);
    hide(els.loading);
    els.cards.innerHTML = "";
    hide(els.empty);

    const user_id_raw = els.userId.value.trim();
    const user_id = parseInt(user_id_raw, 10);
    if (!Number.isFinite(user_id)) {
      els.error.textContent = "Please enter a valid integer user_id.";
      show(els.error);
      return;
    }

    const top_n = parseInt(els.topN.value, 10);
    const minNutrition = els.minNutrition.value.trim() === "" ? null : parseFloat(els.minNutrition.value);
    const maxCalories = els.maxCalories.value.trim() === "" ? null : parseFloat(els.maxCalories.value);
    const refRecipeId = els.refRecipeId.value.trim() === "" ? null : parseInt(els.refRecipeId.value, 10);

    const payload = {
      user_id,
      top_n,
      min_nutrition_score: minNutrition === null || Number.isNaN(minNutrition) ? null : minNutrition,
      max_calories: maxCalories === null || Number.isNaN(maxCalories) ? null : maxCalories,
      ref_recipe_id: refRecipeId === null || Number.isNaN(refRecipeId) ? null : refRecipeId,
    };

    Object.keys(payload).forEach((k) => {
      if (payload[k] === null) delete payload[k];
    });

    renderResultMeta(user_id, top_n);
    setStatus("Requesting recommendations…");
    show(els.loading);

    try {
      const data = await postRecommend(payload);
      hide(els.loading);
      setStatus("Recommendations loaded.");
      renderCards(data.recommendations);
    } catch (err) {
      hide(els.loading);
      setStatus("Error loading recommendations.", true);
      els.error.textContent = String(err.message || err);
      show(els.error);
    }
  }

  function renderEvalChart() {
    const models = ["ALS", "BPR", "SVD", "NCF", "CBF_TFIDF"];
    const hr10 = [0.4654, 0.3643, 0.5140, 0.5201, 0.2312];

    if (window.Chart) {
      const ctx = $("#hr10Chart");
      const ncfIdx = models.indexOf("NCF");
      const colors = models.map((_, i) => (i === ncfIdx ? "rgba(110,168,254,0.95)" : "rgba(230,237,247,0.22)"));

      new window.Chart(ctx, {
        type: "bar",
        data: {
          labels: models,
          datasets: [
            {
              label: "HR@10",
              data: hr10,
              backgroundColor: colors,
              borderColor: colors,
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: "rgba(230,237,247,0.75)" },
            },
            y: {
              beginAtZero: true,
              grid: { color: "rgba(255,255,255,0.08)" },
              ticks: { color: "rgba(230,237,247,0.75)" },
            },
          },
        },
      });
    } else {
      $("#hr10Chart").insertAdjacentHTML(
        "afterbegin",
        `<div class="small-muted">Chart.js not loaded. HR@10: ALS 0.4654, BPR 0.3643, SVD 0.5140, NCF 0.5201, CBF_TFIDF 0.2312</div>`
      );
    }
  }

  function bootstrap() {
    // stats
    fetchStats().then(renderStats).catch(() => {
      els.statTotalRecipes.textContent = "Statistics unavailable";
      els.statTotalUsers.textContent = "-";
      els.statTotalInteractions.textContent = "-";
      els.statSparsity.textContent = "-";
    });

    // chart
    renderEvalChart();

    setActiveTab("demo");
    els.topNValue.textContent = els.topN.value;

    els.tabDemo?.addEventListener("click", () => setActiveTab("demo"));
    els.tabEval?.addEventListener("click", () => setActiveTab("eval"));

    els.topN?.addEventListener("input", () => {
      els.topNValue.textContent = els.topN.value;
    });

    els.form?.addEventListener("submit", onSubmit);


  }

  bootstrap();
})();

