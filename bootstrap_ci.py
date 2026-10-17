"""
bootstrap_ci.py
---------------
Paired bootstrap 95% confidence intervals for the Recall@k difference between
the baseline (Contriever + PPR) and the no-graph variant, computed from the
stored per-query results. Does NOT re-run retrieval.

Usage:
    python bootstrap_ci.py
"""
import json
import random

K_LIST = [2, 5, 10]
N_BOOT = 10000
SEED = 0


def load(path):
    with open(path) as f:
        return json.load(f)


def main():
    base = load("results/baseline_ppr.json")
    var = load("results/variant_no_graph.json")
    assert len(base) == len(var), "result files differ in length"
    assert all(a["id"] == b["id"] for a, b in zip(base, var)), "query ids not aligned"
    n = len(base)
    rng = random.Random(SEED)
    lines = [f"Paired bootstrap, n={n} queries, {N_BOOT} resamples, seed={SEED}"]
    for k in K_LIST:
        diffs = [a["recall"][str(k)] - b["recall"][str(k)] for a, b in zip(base, var)]
        mean = sum(diffs) / n
        boots = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(N_BOOT))
        lo, hi = boots[int(0.025 * N_BOOT)], boots[int(0.975 * N_BOOT) - 1]
        wins = sum(d > 0 for d in diffs)
        losses = sum(d < 0 for d in diffs)
        lines.append(
            f"R@{k}: mean diff (PPR - no-graph) = {mean:+.4f}, "
            f"95% CI [{lo:+.4f}, {hi:+.4f}]; queries improved={wins}, worsened={losses}"
        )
    text = "\n".join(lines)
    print(text)
    with open("results/bootstrap_ci.txt", "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
