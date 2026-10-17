# Repository Architecture

This repo contains an analysis of stored results, not the retrieval pipeline
itself.

## Data flow

1. `results/baseline_ppr.json` and `results/variant_no_graph.json` hold
   per-query outputs for 1,000 MuSiQue dev queries: one run with PPR graph
   reasoning (baseline) and one with Contriever only (variant). Each record
   has the query `id` and a `recall` dictionary keyed by k.
2. `compute_recall.py` averages the stored recall values for k = 2, 5, 10 and
   writes `results/comparison_chart.png`.
3. `bootstrap_ci.py` pairs the two files by query `id` and computes a 95%
   paired bootstrap confidence interval for the recall difference, written to
   `results/bootstrap_ci.txt`.
4. `.github/workflows/check.yml` runs both scripts on every push.

## What is not in this repo

- The code that produced the two JSON files (HippoRAG's original pipeline).
  See the Provenance section in the README.
- The knowledge graph and indexes.

## Files

| File | Purpose |
| --- | --- |
| `README.md` | Results, how to reproduce, limitations, provenance |
| `paper.md` | Full write-up |
| `compute_recall.py` | Recall@k from stored results, bar chart |
| `bootstrap_ci.py` | Paired bootstrap confidence intervals |
| `requirements.txt` | Python dependencies |