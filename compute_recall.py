
import json

k_list = [2, 5, 10]

def compute_recall(filepath, label):
    with open(filepath) as f:
        results = json.load(f)
    n = len(results)
    totals = {k: 0 for k in k_list}
    for sample in results:
        for k in k_list:
            totals[k] += sample['recall'][str(k)]
    print(f"{label} — {n} queries")
    for k in k_list:
        print(f"R@{k}: {totals[k]/n:.4f}")
    return {k: totals[k]/n for k in k_list}

baseline = compute_recall('results/baseline_ppr.json', "BASELINE (Contriever + PPR)")
variant = compute_recall('results/variant_no_graph.json', "VARIANT (Contriever + No-Graph)")
