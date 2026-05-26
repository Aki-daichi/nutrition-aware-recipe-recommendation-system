// Dashboard JavaScript - API Integration and Interactivity

const API_BASE = "http://localhost:8000/api";

// ==================== Page Navigation ====================
document.addEventListener("DOMContentLoaded", () => {
    initializeNavigation();
    loadDashboardData();
});

function initializeNavigation() {
    const navBtns = document.querySelectorAll(".nav-btn");
    navBtns.forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const pageId = btn.getAttribute("data-page");
            showPage(pageId);

            // Update active state
            navBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
        });
    });
}

function showPage(pageId) {
    const pages = document.querySelectorAll(".page");
    pages.forEach(page => page.classList.remove("active"));

    const page = document.getElementById(pageId);
    if (page) {
        page.classList.add("active");

        // Load data specific to the page
        switch (pageId) {
            case "home":
                loadDashboardData();
                break;
            case "recommendations":
                setupRecommendationForm();
                break;
            case "evaluation":
                loadEvaluationData();
                break;
            case "recipes":
                setupRecipesPage();
                break;
        }
    }
}

// ==================== Dashboard Data ====================
async function loadDashboardData() {
    try {
        // Load statistics
        const statsResponse = await fetch(`${API_BASE}/evaluation/recommendations-by-user`);
        if (statsResponse.ok) {
            const stats = await statsResponse.json();
            updateStatistics(stats);
        }

        // Load evaluation metrics
        const metricsResponse = await fetch(`${API_BASE}/evaluation/metrics`);
        if (metricsResponse.ok) {
            const metrics = await metricsResponse.json();
            displayMetricsOnDashboard(metrics);
        }

        // Initialize charts
        initializeDashboardCharts();
    } catch (error) {
        console.error("Error loading dashboard data:", error);
    }
}

function updateStatistics(stats) {
    document.getElementById("total-recommendations").textContent = stats.total_recommendations || 0;
    document.getElementById("total-rated").textContent = stats.total_rated || 0;
    document.getElementById("average-rating").textContent = (stats.average_rating || 0).toFixed(1);
    document.getElementById("active-users").textContent = stats.unique_users || 0;
}

function displayMetricsOnDashboard(metrics) {
    // This can be extended to show metrics on the dashboard
    console.log("Metrics loaded:", metrics);
}

// ==================== Charts ====================
let ratingChart, performanceChart;

function initializeDashboardCharts() {
    // Rating Distribution Chart
    const ratingCtx = document.getElementById("ratingChart");
    if (ratingCtx) {
        if (ratingChart) ratingChart.destroy();

        ratingChart = new Chart(ratingCtx, {
            type: "doughnut",
            data: {
                labels: ["5 Stars", "4 Stars", "3 Stars", "2 Stars", "1 Star"],
                datasets: [
                    {
                        data: [30, 25, 20, 15, 10],
                        backgroundColor: [
                            "#10b981",
                            "#3b82f6",
                            "#f59e0b",
                            "#f97316",
                            "#ef4444",
                        ],
                        borderColor: "#ffffff",
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: "bottom",
                    },
                },
            },
        });
    }

    // Performance Metrics Chart
    const performanceCtx = document.getElementById("performanceChart");
    if (performanceCtx) {
        if (performanceChart) performanceChart.destroy();

        performanceChart = new Chart(performanceCtx, {
            type: "radar",
            data: {
                labels: ["Accuracy", "Precision", "Recall", "F1-Score", "RMSE"],
                datasets: [
                    {
                        label: "Current Model",
                        data: [85, 82, 78, 80, 0.65],
                        borderColor: "#6366f1",
                        backgroundColor: "rgba(99, 102, 241, 0.1)",
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: "top",
                    },
                },
                scales: {
                    r: {
                        min: 0,
                        max: 100,
                    },
                },
            },
        });
    }
}

// ==================== Recommendations ====================
function setupRecommendationForm() {
    const form = document.getElementById("recommendation-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const userId = document.getElementById("user-id").value;
        const numRecs = document.getElementById("num-recommendations").value;

        if (!userId) {
            showAlert("Please enter a User ID", "error");
            return;
        }

        await getRecommendations(userId, parseInt(numRecs));
    });
}

async function getRecommendations(userId, numRecommendations) {
    const container = document.getElementById("recommendations-container");
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading recommendations...</p></div>';

    try {
        const response = await fetch(`${API_BASE}/recommendations`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: userId,
                num_recommendations: numRecommendations,
            }),
        });

        if (!response.ok) {
            throw new Error("Failed to get recommendations");
        }

        const data = await response.json();
        displayRecommendations(data.recommendations || []);
    } catch (error) {
        console.error("Error fetching recommendations:", error);
        container.innerHTML = `<div class="error">Error loading recommendations: ${error.message}</div>`;
    }
}

function displayRecommendations(recommendations) {
    const container = document.getElementById("recommendations-container");

    if (recommendations.length === 0) {
        container.innerHTML = "<p>No recommendations available.</p>";
        return;
    }

    container.innerHTML = recommendations
        .map(
            (rec) => `
        <div class="recommendation-card">
            <div class="recipe-score">Score: ${(rec.score * 100).toFixed(0)}%</div>
            <h3 class="recipe-title">${rec.recipe_name}</h3>
            <p class="recipe-description">${rec.reasoning || "This recipe matches your preferences."}</p>
            <div class="rating-section">
                <span>Rate this recommendation:</span>
                <div class="stars" data-rec-id="${rec.id}">
                    ${[1, 2, 3, 4, 5].map((star) => `<span class="star" data-rating="${star}">★</span>`).join("")}
                </div>
            </div>
        </div>
    `
        )
        .join("");

    // Add rating event listeners
    document.querySelectorAll(".star").forEach((star) => {
        star.addEventListener("click", (e) => {
            const recId = e.target.parentElement.getAttribute("data-rec-id");
            const rating = e.target.getAttribute("data-rating");
            rateRecommendation(recId, rating);
        });
    });
}

async function rateRecommendation(recId, rating) {
    try {
        const response = await fetch(`${API_BASE}/recommendations/${recId}/rate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_rating: parseFloat(rating),
            }),
        });

        if (response.ok) {
            showAlert("Rating recorded successfully!", "success");
        }
    } catch (error) {
        console.error("Error rating recommendation:", error);
        showAlert("Error recording rating", "error");
    }
}

// ==================== Evaluation ====================
async function loadEvaluationData() {
    try {
        const response = await fetch(`${API_BASE}/evaluation/metrics`);

        if (!response.ok) {
            showAlert("No evaluation data available yet", "error");
            return;
        }

        const metrics = await response.json();
        displayEvaluationMetrics(metrics);
        initializeEvaluationChart();
    } catch (error) {
        console.error("Error loading evaluation data:", error);
        showAlert("Error loading evaluation metrics", "error");
    }
}

function displayEvaluationMetrics(metrics) {
    document.getElementById("metric-accuracy").textContent = metrics.accuracy ? `${(metrics.accuracy * 100).toFixed(2)}%` : "-";
    document.getElementById("metric-precision").textContent = metrics.precision ? `${(metrics.precision * 100).toFixed(2)}%` : "-";
    document.getElementById("metric-recall").textContent = metrics.recall ? `${(metrics.recall * 100).toFixed(2)}%` : "-";
    document.getElementById("metric-f1").textContent = metrics.f1_score ? `${(metrics.f1_score * 100).toFixed(2)}%` : "-";
    document.getElementById("metric-rmse").textContent = metrics.rmse ? metrics.rmse.toFixed(4) : "-";
    document.getElementById("metric-mae").textContent = metrics.mae ? metrics.mae.toFixed(4) : "-";
}

function initializeEvaluationChart() {
    const chartCtx = document.getElementById("metricsTimelineChart");
    if (chartCtx) {
        new Chart(chartCtx, {
            type: "line",
            data: {
                labels: ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"],
                datasets: [
                    {
                        label: "Accuracy",
                        data: [75, 78, 80, 82, 85],
                        borderColor: "#6366f1",
                        backgroundColor: "rgba(99, 102, 241, 0.1)",
                        tension: 0.4,
                    },
                    {
                        label: "Precision",
                        data: [72, 75, 78, 80, 82],
                        borderColor: "#10b981",
                        backgroundColor: "rgba(16, 185, 129, 0.1)",
                        tension: 0.4,
                    },
                    {
                        label: "Recall",
                        data: [70, 73, 75, 77, 78],
                        borderColor: "#f59e0b",
                        backgroundColor: "rgba(245, 158, 11, 0.1)",
                        tension: 0.4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: "top",
                    },
                },
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                    },
                },
            },
        });
    }
}

// ==================== Recipes ====================
function setupRecipesPage() {
    const btn = document.getElementById("load-recipes-btn");
    if (btn) {
        btn.addEventListener("click", loadRecipes);
    }
}

async function loadRecipes() {
    const container = document.getElementById("recipes-container");
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading recipes...</p></div>';

    try {
        const response = await fetch(`${API_BASE}/recipes?skip=0&limit=20`);

        if (!response.ok) {
            throw new Error("Failed to load recipes");
        }

        const recipes = await response.json();
        displayRecipes(recipes);
    } catch (error) {
        console.error("Error loading recipes:", error);
        container.innerHTML = `<div class="error">Error loading recipes: ${error.message}</div>`;
    }
}

function displayRecipes(recipes) {
    const container = document.getElementById("recipes-container");

    if (recipes.length === 0) {
        container.innerHTML = "<p>No recipes available.</p>";
        return;
    }

    container.innerHTML = recipes
        .map(
            (recipe) => `
        <div class="recipe-card">
            <h3 class="recipe-title">${recipe.name}</h3>
            <p class="recipe-description">${recipe.description || "No description available"}</p>
            
            <div class="recipe-nutrients">
                ${recipe.calories ? `<div class="nutrient"><div class="nutrient-label">Calories</div><div class="nutrient-value">${recipe.calories}</div></div>` : ""}
                ${recipe.protein ? `<div class="nutrient"><div class="nutrient-label">Protein (g)</div><div class="nutrient-value">${recipe.protein.toFixed(1)}</div></div>` : ""}
                ${recipe.carbs ? `<div class="nutrient"><div class="nutrient-label">Carbs (g)</div><div class="nutrient-value">${recipe.carbs.toFixed(1)}</div></div>` : ""}
                ${recipe.fat ? `<div class="nutrient"><div class="nutrient-label">Fat (g)</div><div class="nutrient-value">${recipe.fat.toFixed(1)}</div></div>` : ""}
            </div>
            
            <div style="color: #6b7280; font-size: 0.9rem;">
                ${recipe.difficulty ? `<p>Difficulty: <strong>${recipe.difficulty}</strong></p>` : ""}
                ${recipe.cooking_time ? `<p>Cooking Time: <strong>${recipe.cooking_time} min</strong></p>` : ""}
                ${recipe.servings ? `<p>Servings: <strong>${recipe.servings}</strong></p>` : ""}
            </div>
        </div>
    `
        )
        .join("");
}

// ==================== Utility Functions ====================
function showAlert(message, type = "info") {
    const alert = document.createElement("div");
    alert.className = type;
    alert.textContent = message;
    alert.style.position = "fixed";
    alert.style.top = "20px";
    alert.style.right = "20px";
    alert.style.zIndex = "1000";
    alert.style.maxWidth = "400px";

    document.body.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 5000);
}
