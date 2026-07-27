"""
compute_recall.py
------------------
Computes Recall@k for both the baseline (Contriever + PPR graph reasoning)
and the no-graph variant, on the same 1,000 MuSiQue dev queries.
Also generates a comparison bar chart for the README.

Usage:
    python compute_recall.py
"""
import json
import matplotlib.pyplot as plt

K_LIST = [2, 5, 10]


def compute_recall(filepath, label):
    with open(filepath) as f:
        results = json.load(f)
    n = len(results)
    totals = {k: 0 for k in K_LIST}
    for sample in results:
        for k in K_LIST:
            totals[k] += sample["recall"][str(k)]
    print(f"{label} — {n} queries")
    for k in K_LIST:
        print(f"  R@{k}: {totals[k] / n:.4f}")
    return {k: totals[k] / n for k in K_LIST}


def plot_comparison(baseline, variant):
    x = [f"R@{k}" for k in K_LIST]
    baseline_vals = [baseline[k] for k in K_LIST]
    variant_vals = [variant[k] for k in K_LIST]

    width = 0.35
    positions = range(len(x))

    plt.figure(figsize=(6, 4))
    plt.bar([p - width / 2 for p in positions], baseline_vals, width,
            label="Contriever + PPR (Baseline)", color="#2b6cb0")
    plt.bar([p + width / 2 for p in positions], variant_vals, width,
            label="Contriever Only (No-Graph)", color="#888888")
    plt.xticks(list(positions), x)
    plt.ylabel("Recall")
    plt.title("HippoRAG Ablation: Graph vs. No-Graph\n(MuSiQue dev, n=1000)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("results/comparison_chart.png", dpi=150)
    print("\nSaved results/comparison_chart.png")


if __name__ == "__main__":
    baseline = compute_recall("results/baseline_ppr.json", "BASELINE (Contriever + PPR)")
    variant = compute_recall("results/variant_no_graph.json", "VARIANT (Contriever + No-Graph)")
    plot_comparison(baseline, variant)
