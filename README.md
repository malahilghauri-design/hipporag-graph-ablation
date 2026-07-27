# HippoRAG Ablation: Graph vs. No-Graph Retrieval on MuSiQue

Controlled ablation study isolating the contribution of Personalized
PageRank (PPR) graph reasoning in [HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG)
(Jiménez Gutiérrez et al., NeurIPS 2024) on the MuSiQue multi-hop QA benchmark.

📄 **[Read the full paper →](./paper.md)**

## Key Finding

Removing PPR-based graph reasoning causes a **21.02% drop in Recall@10**,
confirming that graph-based multi-hop reasoning — not the underlying
encoder — is the primary driver of HippoRAG's performance.

## Results (n=1,000 queries, MuSiQue dev)

| Metric | Contriever + PPR (Baseline) | Contriever Only (Variant) | Δ |
|--------|------------------------------|------------------------------|---|
| R@2    | 0.3276                       | 0.2995                       | −8.58% |
| R@5    | 0.4037                       | 0.3344                       | −17.17% |
| R@10   | 0.4467                       | 0.3528                       | −21.02% |

![Recall Comparison Chart](./results/comparison_chart.png)

## Repository Structure

```
hipporag-graph-ablation/
├── README.md               # this file
├── paper.md                 # full write-up (abstract, method, related work, analysis)
├── compute_recall.py         # recomputes Recall@k and regenerates the chart
├── requirements.txt
└── results/
    ├── baseline_ppr.json         # per-query results, Contriever + PPR
    ├── variant_no_graph.json     # per-query results, Contriever only
    └── comparison_chart.png      # generated bar chart
```

## How to Reproduce

```bash
git clone https://github.com/malahilghauri-design/hipporag-graph-ablation.git
cd hipporag-graph-ablation
pip install -r requirements.txt
python compute_recall.py
```

This recomputes Recall@2/5/10 directly from the stored per-query result files
and regenerates `results/comparison_chart.png`.

## Citation

Built on top of [HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG) (NeurIPS 2024):

> Jiménez Gutiérrez, B., et al. (2024). *HippoRAG: Neurobiologically Inspired
> Long-Term Memory for Large Language Models.* NeurIPS 2024.
