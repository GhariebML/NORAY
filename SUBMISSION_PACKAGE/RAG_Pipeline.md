# Hybrid RAG Pipeline Technical Deep-Dive

---

## 🔍 Ingestion & Retrieval Workflow

```mermaid
graph TD
    File[Uploaded File] --> Clean[Text Preprocessing & Normalization]
    Clean --> Chunk[Recursive Character Chunker]
    Chunk --> DenseEmbed[SentenceTransformers: all-MiniLM-L6-v2]
    Chunk --> SparseIndex[BM25 Tokenizer]
    DenseEmbed --> Qdrant[(Qdrant Vector DB)]
    SparseIndex --> BM25File[(BM25 Pickle Storage)]
    
    Query[User Query] --> DenseSearch[Qdrant Cosine Similarity Search]
    Query --> SparseSearch[BM25 Lexical Keyword Search]
    DenseSearch & SparseSearch --> RRF[Reciprocal Rank Fusion]
    RRF --> Reranker[Cross-Encoder Reranker]
    Reranker --> Compressor[ContextCompressor: Merging Chunks]
    Compressor --> Prompt[LLM Prompt Ingestion Window]
```

---

## 📐 Mathematical Formulation

### Reciprocal Rank Fusion (RRF)
Given document set $D$ and rank positions $R_m(d)$ from retriever engines $m \in \{Dense, Sparse\}$:

$$RRF\_Score(d \in D) = \sum_{m \in M} \frac{1}{k + R_m(d)}$$

Where constant $k = 60$. RRF balances high-precision vector matches with exact lexical keyword hits.
