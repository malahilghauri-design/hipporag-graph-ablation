# hipporag-graph-ablation
"Ablation study on PPR-based graph reasoning in HippoRAG using MuSiQue dataset"
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

## Repository Structure
