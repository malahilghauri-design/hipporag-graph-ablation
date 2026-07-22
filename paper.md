Graph Matters: Ablation Study on the Role of Personalized PageRank in HippoRAG for Multi-Hop Question Answering
Authors: Malahil Ghauri
Affiliation: Islamia university bahawalpur
Date: July 2025
Track: Reproducibility & Ablation Study
Original Work: HippoRAG — Bernal Jiménez Gutiérrez et al., NeurIPS 2024
Original Repository: github.com/OSU-NLP-Group/HippoRAG

Abstract
HippoRAG is a neurobiologically-inspired retrieval-augmented generation (RAG) framework that simulates the hippocampal memory system of the human brain. It augments standard dense retrieval with a knowledge graph and Personalized PageRank (PPR) to enable multi-hop reasoning over retrieved passages. In this work, we conduct a controlled ablation study to isolate the contribution of the graph-based retrieval component. We compare the full HippoRAG pipeline — using the Contriever dense encoder with PPR graph re-ranking — against a graph-free variant that uses only Contriever's vector similarity for retrieval. Both systems are evaluated on 1,000 queries from the MuSiQue benchmark. Our results demonstrate that removing the graph component causes a −21.02% drop in Recall@10, confirming that the PPR graph-reasoning module is the primary driver of HippoRAG's performance gains over vanilla dense retrieval.

1. Introduction
Retrieval-Augmented Generation (RAG) has become the dominant paradigm for grounding large language model (LLM) outputs in external knowledge. However, standard RAG pipelines rely on vector similarity search, which retrieves passages independently and fails to model the multi-hop relationships between facts — a critical requirement for complex QA.

HippoRAG (Jiménez Gutiérrez et al., 2024) draws inspiration from the hippocampal-neocortical memory system, where the hippocampus indexes associations between concepts rather than storing raw facts. The system:

Extracts named entities (via an LLM) from each passage to build nodes in a knowledge graph.
Infers edges between co-occurring entities within passages.
At query time, retrieves seed passages via dense retrieval, then propagates scores through the graph using Personalized PageRank (PPR) to surface related passages that a vector search would miss.
While HippoRAG demonstrates strong performance on multi-hop QA benchmarks (HotpotQA, 2WikiMultiHopQA, MuSiQue), a key open question is: how much of the gain comes from the graph reasoning vs. the choice of underlying dense encoder?

To answer this, we design a minimal ablation: we strip out the PPR graph re-ranking and use the identical Contriever encoder in a standard dense-retrieval mode. This isolates the graph's contribution cleanly, without changing any other hyperparameter.

2. Background
2.1 HippoRAG Architecture
HippoRAG operates in two phases:

Offline Indexing:

Each passage is processed by an LLM (GPT-3.5-turbo by default; we use the same configuration) to extract named entities.
A knowledge graph 
G
=
(
V
,
E
)
G=(V,E) is constructed where:
V
V = extracted named entities (nodes)
E
E = co-occurrence edges between entities appearing in the same passage
Each passage is also encoded into a dense vector using the Contriever encoder.
Online Retrieval:

The query is encoded with Contriever to retrieve top-
k
k seed passages.
Seed entities are identified and used as personalization nodes in PPR.
PPR scores propagate through 
G
G, re-ranking passages by their graph-weighted relevance to the query.
2.2 Personalized PageRank (PPR)
PPR computes a stationary distribution 
π
π of a random walk that, at each step, either:

Follows a graph edge with probability 
1
−
α
1−α, or
Teleports back to the seed set with probability 
α
α.
Formally:

π
=
α
⋅
v
+
(
1
−
α
)
⋅
A
T
π
π=α⋅v+(1−α)⋅A 
T
 π
where 
v
v is the personalization vector (uniform over seed entities), 
A
A is the column-normalized adjacency matrix, and 
α
=
0.15
α=0.15 (standard damping factor). Passages linked to high-scoring entities are surfaced as additional candidates.

2.3 MuSiQue Benchmark
MuSiQue (Multi-hop Sequential Questions) is a challenging multi-hop QA dataset where each question requires 2–4 sequential reasoning steps across multiple documents. It is designed to resist single-hop shortcuts, making it an ideal testbed for graph-based retrieval methods.

Scale: 20,000 training + 2,417 development questions
Evaluation subset used: 1,000 queries (random sample from development set)
Metric: Recall@
k
k — whether the gold supporting passage appears in the top-
k
k retrieved results
3. Experimental Setup
3.1 Models and Components
Component	Baseline (HippoRAG)	Variant (No-Graph)
Dense Encoder	Contriever (facebook/contriever)	Contriever (facebook/contriever)
Graph Construction LLM	GPT-3.5-turbo	— (not used)
Graph Ranking	Personalized PageRank (α=0.15)	✗ Disabled
Retrieval Method	Dense + PPR re-rank	Dense only (cosine similarity)
Embedding Dim	768	768
Note on LLM Usage: GPT-3.5-turbo (gpt-3.5-turbo-1106) is used only in the baseline for offline knowledge graph construction (entity and relation extraction). It is not involved in the retrieval process itself. The No-Graph variant skips this step entirely since there is no graph to build.

3.2 Contriever
Contriever (Izacard et al., 2022) is an unsupervised dense retrieval encoder trained via contrastive learning on web data, without any labeled QA pairs. It produces 768-dimensional vectors and has been widely adopted as a strong zero-shot baseline for open-domain QA retrieval.

3.3 Hyperparameters
Hyperparameter	Value
Retrieval top-k (dense seed)	10
PPR damping factor α	0.15
PPR iterations	100
Max passages per query	10
Evaluation queries	1,000
Dataset split	MuSiQue dev
3.4 Evaluation Metric
We report Recall@k (R@k), defined as:

R
@
k
=
1
∣
Q
∣
∑
q
∈
Q
1
[
gold passage
∈
top-
k
 retrieved for 
q
]
R@k= 
∣Q∣
1
​
  
q∈Q
∑
​
 1[gold passage∈top-k retrieved for q]
We evaluate at 
k
∈
{
2
,
5
,
10
}
k∈{2,5,10} to capture performance across different retrieval budgets.

4. Results
4.1 Main Results Table
Metric	Baseline (Contriever + PPR)	Variant (Contriever + No-Graph)	Δ (Variant − Baseline)	% Change
R@2	0.3276	0.2995	−0.0281	−8.58%
R@5	0.4037	0.3344	−0.0693	−17.17%
R@10	0.4467	0.3528	−0.0939	−21.02%
Both runs evaluated on the same 1,000 MuSiQue dev queries. Higher is better.

4.2 Key Observations
1. Graph reasoning is critical, not incremental.
The PPR component provides a 21.02% improvement in R@10 over the identical encoder used without graph re-ranking. This is not a marginal improvement — it is a fundamental architectural contribution.

2. The gap widens with larger retrieval budgets.
The performance gap increases from −8.58% at R@2 to −21.02% at R@10. This pattern suggests that PPR is particularly effective at recovering relevant passages at deeper ranks — documents that vector similarity ranks low but that are semantically connected via graph edges to high-scoring seed passages.

3. Dense retrieval alone fails at multi-hop reasoning.
The No-Graph variant achieves only R@10 = 0.3528, meaning 64.7% of queries fail to retrieve a gold passage even in the top 10 results. HippoRAG's graph raises this to 55.3% missing — still significant room for improvement, but a clear advancement.

4.3 Analysis: Why Does PPR Help?
On MuSiQue, a typical question might be:

"What is the capital of the country where [Person X] was born?"

This requires finding:

A passage mentioning where Person X was born → country Y
A separate passage stating the capital of country Y
A vector-only search on the query will likely retrieve passages about Person X but may rank the capital passage much lower. PPR, however, propagates the score from "country Y" (an entity linked to retrieved passages) through the graph to surface the capital passage — exactly the multi-hop bridge that dense retrieval misses.

5. Related Work
HippoRAG (Jiménez Gutiérrez et al., 2024): Original paper proposing the hippocampal memory analogy for LLM retrieval using PPR on entity knowledge graphs.
Contriever (Izacard et al., 2022): Unsupervised dense retrieval via contrastive learning, strong zero-shot baseline.
DPR (Karpukhin et al., 2020): Supervised dense passage retrieval for open-domain QA.
GraphRAG (Edge et al., 2024): Microsoft's approach to graph-enhanced RAG using community detection.
MuSiQue (Trivedi et al., 2022): Multi-hop sequential QA benchmark designed to prevent reasoning shortcuts.
Personalized PageRank (Page et al., 1999): Random walk-based authority scoring with query-specific teleportation.
6. Discussion
6.1 Limitations
Single dataset: We evaluate only on MuSiQue. Performance patterns on HotpotQA and 2WikiMultiHopQA (which have shorter reasoning chains) may differ.
LLM dependency: The graph construction step uses GPT-3.5-turbo, which adds API cost and introduces variability based on entity extraction quality.
Scale: 1,000 queries is a representative sample but not the full dev set. Results may vary slightly on the full evaluation.
6.2 Implications
Our results have two practical implications:

For practitioners: If deploying HippoRAG, do not skip graph construction to save compute — you lose ~21% retrieval coverage at rank 10 on complex multi-hop queries.
For researchers: The PPR component is the key algorithmic innovation. Future work could explore alternative graph ranking methods (e.g., HITS, community-weighted walk) or dynamic graph updates to further improve upon it.
7. Conclusion
We present a clean, reproducible ablation study showing that the knowledge graph + Personalized PageRank component of HippoRAG is responsible for 8.6–21.0% improvement in Recall on MuSiQue multi-hop QA. The graph-free variant using the same Contriever encoder scores substantially lower across all retrieval budgets, confirming that HippoRAG's architectural novelty — not its encoder choice — drives its gains. This validates the core thesis of the original paper and provides a quantitative foundation for future graph-augmented retrieval research.

References
Jiménez Gutiérrez, B., et al. (2024). HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models. NeurIPS 2024.
Izacard, G., et al. (2022). Unsupervised Dense Information Retrieval with Contrastive Learning. TMLR 2022.
Trivedi, H., et al. (2022). MuSiQue: Multihop Questions via Single-hop Question Composition. TACL 2022.
Page, L., et al. (1999). The PageRank Citation Ranking: Bringing Order to the Web. Stanford Technical Report.
Karpukhin, V., et al. (2020). Dense Passage Retrieval for Open-Domain Question Answering. EMNLP 2020.
Edge, D., et al. (2024). From Local to Global: A Graph RAG Approach to Query-Focused Summarization. arXiv:2404.16130.
Appendix A: Reproduction Steps
bash

# 1. Clone HippoRAG
git clone https://github.com/OSU-NLP-Group/HippoRAG
cd HippoRAG
pip install -r requirements.txt
# 2. Set your OpenAI key (needed for graph construction in baseline)
export OPENAI_API_KEY=your_key_here
# 3. Run BASELINE (Contriever + PPR) on MuSiQue
python src/hipporag/main.py \
  --dataset musique \
  --retriever contriever \
  --graph_alg ppr \
  --num_examples 1000
# 4. Run VARIANT (Contriever + No-Graph)
python src/hipporag/main.py \
  --dataset musique \
  --retriever contriever \
  --graph_alg none \
  --num_examples 1000
# 5. Evaluate both outputs
python src/hipporag/eval.py --results_path results/baseline/
python src/hipporag/eval.py --results_path results/no_graph/
Appendix B: GitHub README Template
markdown

# HippoRAG Ablation: Graph vs. No-Graph on MuSiQue
Controlled ablation study comparing HippoRAG's full pipeline 
(Contriever + PPR) vs. graph-free dense retrieval (Contriever only) 
on MuSiQue multi-hop QA.
## Results (n=1000 queries, MuSiQue dev)
|
 Metric 
|
 Contriever + PPR 
|
 Contriever Only 
|
 Δ       
|
|
--------
|
-----------------
|
-----------------
|
---------
|
|
 R@2    
|
 0.3276          
|
 0.2995          
|
 −8.58%  
|
|
 R@5    
|
 0.4037          
|
 0.3344          
|
 −17.17% 
|
|
 R@10   
|
 0.4467          
|
 0.3528          
|
 −21.02% 
|
## Key Finding
The PPR graph component accounts for up to 21% improvement in 
retrieval recall. Graph-free dense retrieval fails at multi-hop 
reasoning that requires bridging across separate documents.
## Setup
See [paper](./paper.md) for full experimental details.
Built on top of [HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG) (NeurIPS 2024).
