# ablation/visualize_pareto.py
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CSV_PATH = PROJECT_ROOT / "ablation" / "outputs" / "results" / "ablation_study_results.csv"
OUTPUT_DIR = PROJECT_ROOT / "ablation" / "outputs" / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def parse_weights(model_name):
    # Match pattern like: Hybrid (cf=0.6, cbf=0.2, nutr=0.2)
    match = re.search(r"Hybrid \(cf=([\d.]+), cbf=([\d.]+), nutr=([\d.]+)\)", model_name)
    if match:
        return float(match.group(1)), float(match.group(2)), float(match.group(3))
    return None

def main():
    print(f"Reading ablation results from {CSV_PATH}...")
    if not CSV_PATH.exists():
        print(f"Error: {CSV_PATH} does not exist. Please run ablation first.")
        return
        
    df = pd.read_csv(CSV_PATH)
    
    # Parse weights for hybrid models
    cf_weights, cbf_weights, nutr_weights = [], [], []
    is_hybrid = []
    
    for idx, row in df.iterrows():
        weights = parse_weights(row['Model'])
        if weights:
            cf_weights.append(weights[0])
            cbf_weights.append(weights[1])
            nutr_weights.append(weights[2])
            is_hybrid.append(True)
        else:
            cf_weights.append(0.0)
            cbf_weights.append(0.0)
            nutr_weights.append(0.0)
            is_hybrid.append(False)
            
    df['w_cf'] = cf_weights
    df['w_cbf'] = cbf_weights
    df['w_nutr'] = nutr_weights
    df['is_hybrid'] = is_hybrid
    
    # Identify Pareto optimal points
    # Objective 1: Maximize HR@10 (Accuracy)
    # Objective 2: Maximize Avg_Nutrition (Health)
    pareto_indices = []
    for i, row_i in df.iterrows():
        dominated = False
        for j, row_j in df.iterrows():
            if i == j:
                continue
            better_in_both = (row_j['HR@10'] >= row_i['HR@10']) and (row_j['Avg_Nutrition'] >= row_i['Avg_Nutrition'])
            strictly_better_in_one = (row_j['HR@10'] > row_i['HR@10']) or (row_j['Avg_Nutrition'] > row_i['Avg_Nutrition'])
            if better_in_both and strictly_better_in_one:
                dominated = True
                break
        if not dominated:
            pareto_indices.append(i)
            
    df_pareto = df.iloc[pareto_indices].sort_values(by='HR@10')
    
    # Clean matplotlib style configuration
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'Inter']
    plt.rcParams['text.color'] = '#2D3748'
    plt.rcParams['axes.labelcolor'] = '#2D3748'
    plt.rcParams['xtick.color'] = '#718096'
    plt.rcParams['ytick.color'] = '#718096'
    
    fig, ax = plt.subplots(figsize=(11, 7.5))
    
    # 1. Plot background grid
    ax.grid(True, linestyle='--', color='#E2E8F0', alpha=0.7, zorder=0)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CBD5E0')
    ax.spines['bottom'].set_color('#CBD5E0')
    
    # 2. Plot non-hybrid baselines
    baselines = df[~df['is_hybrid']]
    ax.scatter(baselines['HR@10'], baselines['Avg_Nutrition'], 
               color='#A0AEC0', s=100, marker='X', label='Baseline Cascades / Pure Models', zorder=2)
               
    # 3. Plot hybrid models (non-Pareto)
    hybrids = df[df['is_hybrid']]
    pareto_model_names = set(df_pareto['Model'])
    non_pareto_hybrids = hybrids[~hybrids['Model'].isin(pareto_model_names)]
    
    ax.scatter(non_pareto_hybrids['HR@10'], non_pareto_hybrids['Avg_Nutrition'], 
               color='#E2E8F0', s=55, alpha=0.5, edgecolors='none', label='Sub-optimal Hybrids', zorder=1)
    
    # 4. Plot Pareto frontier line and fill shaded area under frontier for visual depth
    ax.plot(df_pareto['HR@10'], df_pareto['Avg_Nutrition'], color='#E53E3E', linestyle='-', linewidth=2.5, alpha=0.8, zorder=3)
    ax.fill_between(df_pareto['HR@10'], df_pareto['Avg_Nutrition'], color='#FED7D7', alpha=0.15, zorder=0)
    
    # 5. Plot Pareto optimal points
    ax.scatter(df_pareto['HR@10'], df_pareto['Avg_Nutrition'], 
               color='#E53E3E', s=120, edgecolors='white', linewidths=1.5, label='Pareto Frontier (Optimal)', zorder=4)
    
    # 6. Annotate key points with custom offsets to prevent overlap completely
    annotations_list = [
        {
            "match": lambda row: "1. Pure CF" in row["Model"],
            "label": "Pure CF (NCF) Baseline",
            "xytext": (0, -25),
            "ha": "center",
            "va": "top",
            "color": "#4A5568",
            "arrow_color": "#718096"
        },
        {
            "match": lambda row: "2. Pure CBF" in row["Model"],
            "label": "Pure CBF (TF-IDF) Baseline",
            "xytext": (0, -25),
            "ha": "center",
            "va": "top",
            "color": "#4A5568",
            "arrow_color": "#718096"
        },
        {
            "match": lambda row: "8. Cascade CF -> CBF -> Nutrition Rerank" in row["Model"],
            "label": "Original Hybrid Cascade",
            "xytext": (-30, 25),
            "ha": "right",
            "va": "bottom",
            "color": "#4A5568",
            "arrow_color": "#718096"
        },
        {
            "match": lambda row: row["is_hybrid"] and np.allclose([row["w_cf"], row["w_cbf"], row["w_nutr"]], [0.7, 0.3, 0.0]),
            "label": "Max Accuracy\n(0.7, 0.3, 0.0)",
            "xytext": (30, 25),
            "ha": "left",
            "va": "bottom",
            "color": "#1A202C",
            "arrow_color": "#E53E3E"
        },
        {
            "match": lambda row: row["is_hybrid"] and np.allclose([row["w_cf"], row["w_cbf"], row["w_nutr"]], [0.6, 0.3, 0.1]),
            "label": "Balanced Sweet-Spot\n(0.6, 0.3, 0.1)",
            "xytext": (40, 35),
            "ha": "left",
            "va": "bottom",
            "color": "#1A202C",
            "arrow_color": "#E53E3E"
        },
        {
            "match": lambda row: row["is_hybrid"] and np.allclose([row["w_cf"], row["w_cbf"], row["w_nutr"]], [0.6, 0.2, 0.2]),
            "label": "Nutrition-Heavy\n(0.6, 0.2, 0.2)",
            "xytext": (40, 35),
            "ha": "left",
            "va": "bottom",
            "color": "#1A202C",
            "arrow_color": "#E53E3E"
        },
        {
            "match": lambda row: row["is_hybrid"] and np.allclose([row["w_cf"], row["w_cbf"], row["w_nutr"]], [0.4, 0.0, 0.6]),
            "label": "Max Nutrition\n(0.4, 0.0, 0.6)",
            "xytext": (0, 30),
            "ha": "center",
            "va": "bottom",
            "color": "#1A202C",
            "arrow_color": "#E53E3E"
        }
    ]

    for idx, row in df.iterrows():
        for ann in annotations_list:
            if ann["match"](row):
                arrow = dict(arrowstyle="->", color=ann["arrow_color"], lw=1.0, alpha=0.7)
                ax.annotate(
                    ann["label"],
                    (row['HR@10'], row['Avg_Nutrition']),
                    textcoords="offset points",
                    xytext=ann["xytext"],
                    ha=ann["ha"],
                    va=ann["va"],
                    fontsize=9.5,
                    fontweight='bold',
                    color=ann["color"],
                    arrowprops=arrow
                )
                        
    # Title & Subtitle
    plt.suptitle("Ablation Study Pareto Frontier: Accuracy vs. Healthiness", fontsize=15, fontweight='bold', color='#1A202C', y=0.96, x=0.115, ha='left')
    ax.set_title("Evaluating Weighted Hybrid weights (w_cf, w_cbf, w_nutr) | Target: Balance HR@10 and Avg Nutrition", 
                 fontsize=10.5, color='#4A5568', pad=20, loc='left')
    
    ax.set_xlabel("Recommendation Accuracy (Hit Rate @ 10)", fontsize=11, labelpad=10, fontweight='semibold')
    ax.set_ylabel("Average Nutrition Score of Top-10 Recipes (0 - 100)", fontsize=11, labelpad=10, fontweight='semibold')
    
    # Customizing axes limits and ticks
    ax.set_xlim(0.05, 0.60)
    ax.set_ylim(5, 95)
    
    # Legend
    legend = ax.legend(loc='lower left', frameon=True, facecolor='white', edgecolor='none', fontsize=9.5)
    legend.get_frame().set_boxstyle("round,pad=0.5")
    
    # Informational box
    info_text = (
        "Key Trade-offs:\n"
        "• Adding just 10% Nutrition weight (0.6, 0.3, 0.1)\n"
        "  improves Avg Nutrition from 15.0 to 38.8\n"
        "  with only ~2% drop in HR@10.\n"
        "• 20% Nutrition weight (0.6, 0.2, 0.2) increases\n"
        "  nutrition to 58.2, but drops HR@10 to 0.43."
    )
    props = dict(boxstyle='round,pad=0.6', facecolor='#F7FAFC', edgecolor='#E2E8F0', alpha=0.9)
    ax.text(0.96, 0.95, info_text, transform=ax.transAxes, fontsize=9.5,
            verticalalignment='top', horizontalalignment='right', bbox=props, color='#2D3748', linespacing=1.4)
            
    plot_path = OUTPUT_DIR / "pareto_frontier.png"
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(plot_path, dpi=300)
    print(f"\nPolished Pareto plot saved to: {plot_path}")

if __name__ == "__main__":
    main()
