# RAG Audit

**Project:** NORAY OS
**Audit Date:** July 2026

---

## 1. Current Pipeline Architecture

### 1.1 End-to-End Flow
`mermaid
flowchart TD
    Q[User Query] --> QP[QueryProcessor]
    QP --> IC[Intent Classification]
    QP --> HE[HyDE Expansion]
    QP --> QE[Query Expansion]
    
    IC --> STRATEGY[Retrieval Strategy]
    HE --> STRATEGY
    QE --> STRATEGY
    
    STRATEGY --> DENSE[Dense Vector Search]
    STRATEGY --> SPARSE[BM25 Sparse Search]
    
    DENSE --> RRF[RRF Fusion]
    SPARSE --> RRF
    
    RRF --> RERANK[Cross-Encoder Reranking]
    RERANK --> COMPRESS[Context Compression]
    
    COMPRESS --> CHECK{Sufficient Context?}
    CHECK -->|Yes| INJECT[Context Injection]
    CHECK -->|No| MEM_FALLBACK[Conversation Memory Fallback]
    
    MEM_FALLBACK --> CHECK2{Sufficient?}
    CHECK2 -->|Yes| INJECT
    CHECK2 -->|No| LLM_FALLBACK[LLM-Only Fallback]
    
    LLM_FALLBACK --> INJECT
    INJECT --> LLM[LLM Generation]
    LLM --> RESPONSE[Response with Citations]
`

### 1.2 Pipeline Stages
| Stage | File | Purpose | Status |
|---|---|---|---|
| 1. Query Processing | query_processor.py | Intent + HyDE + expansion | Functional |
| 2. Dense Search | ector_store.py | Semantic similarity | Functional |
| 3. Sparse Search | sparse_index.py | BM25 keyword matching | Functional |
| 4. RRF Fusion | usion.py | Combine dense + sparse | Functional |
| 5. Reranking | eranker.py | Cross-encoder refinement | Functional |
| 6. Compression | compressor.py | Dedup + merge chunks | Functional |
| 7. Fallback | etrieval_pipeline.py | Memory + LLM-only | Functional |

---

## 2. Strengths

| # | Strength | Detail |
|---|---|---|
| 1 | **7-Stage Resilient Pipeline** | Every stage is optional; failure never terminates execution |
| 2 | **Hybrid Search** | Dense (semantic) + Sparse (keyword) provides best of both worlds |
| 3 | **RRF Fusion** | Industry-standard fusion algorithm with configurable k |
| 4 | **Cross-Encoder Reranking** | Significantly improves relevance over bi-encoder alone |
| 5 | **Multiple Embedding Providers** | 6 providers with automatic fallback |
| 6 | **Multiple Reranker Providers** | 3 providers with automatic fallback |
| 7 | **Query Processing** | HyDE + intent classification + query expansion |
| 8 | **Context Compression** | Deduplication + adjacent chunk merging |
| 9 | **Graceful Degradation** | Falls back to memory, then LLM-only |
| 10 | **Knowledge Graph Integration** | GraphRAG enriches vector results with entity relationships |

---

## 3. Weaknesses

| # | Weakness | Severity | Impact |
|---|---|---|---|
| 1 | **Embedding Dimension Mismatch** | Critical | Config defaults ge-m3 (1024-dim) but Qdrant created for 384-dim |
| 2 | **No Incremental Indexing** | High | Full BM25 rebuild required for new documents |
| 3 | **Basic BM25 Tokenization** | Medium | Whitespace-based, no stemming/lemmatization |
| 4 | **No Document Freshness** | Medium | No staleness detection or re-indexing |
| 5 | **Limited Chunking Strategies** | Medium | 4 strategies but no semantic chunking |
| 6 | **No Query Routing** | Medium | Same pipeline for all query types |
| 7 | **No Diversity Enforcement** | Medium | May return redundant chunks |
| 8 | **No Citation Verification** | Medium | Citations not validated against source |
| 9 | **Mocked Universal Retriever** | Low | universal_retriever.py is unused |

---

## 4. Retrieval Flow Detail

### 4.1 Query Processing
`mermaid
flowchart LR
    Q[Raw Query] --> CLASSIFY[Intent Classification]
    CLASSIFY --> HYDE[HyDE Generation]
    HYDE --> EXPAND[Query Expansion]
    EXPAND --> OUT[Processed Query]
    
    CLASSIFY --> STRATEGY[Strategy Selection]
    STRATEGY --> DENSE_WEIGHT[Dense Weight]
    STRATEGY --> SPARSE_WEIGHT[Sparse Weight]
`

| Feature | Implementation | Status |
|---|---|---|
| Intent Classification | LLM-based query categorization | Functional |
| HyDE | Generate hypothetical answer, embed that | Functional |
| Query Expansion | LLM-based synonym expansion | Functional |
| Strategy Selection | Map intent to retrieval weights | Functional |

### 4.2 Dense Search
| Parameter | Value | Notes |
|---|---|---|
| Backend | Qdrant (primary), FAISS (fallback) | Auto-selected |
| Distance Metric | Cosine similarity | Standard |
| Top-K | Configurable | Default varies |
| Score Threshold | Configurable | Optional filtering |

### 4.3 Sparse Search (BM25)
| Parameter | Value | Notes |
|---|---|---|
| Library | rank_bm25 | Python implementation |
| Tokenization | Whitespace | Basic |
| Index Format | Pickle serialized | File-based |
| Update Strategy | Full rebuild | No incremental |

### 4.4 RRF Fusion
| Parameter | Value | Notes |
|---|---|---|
| Algorithm | Reciprocal Rank Fusion | Standard |
| k parameter | 60 (default) | Tunable |
| Score Formula | 1 / (k + rank) | Standard |

---

## 5. Embedding Flow

### 5.1 Embedding Pipeline
`mermaid
flowchart LR
    DOC[Document] --> CHUNK[Chunking]
    CHUNK --> EMBED[Embedding]
    EMBED --> STORE[Vector Store]
    
    STORE --> QDRANT[Qdrant]
    STORE --> FAISS[FAISS Fallback]
`

### 5.2 Chunking Strategies
| Strategy | File | Use Case | Status |
|---|---|---|---|
| Recursive | chunker.py | General documents | Functional |
| Markdown | chunker.py | Markdown files | Functional |
| Code | chunker.py | Source code | Functional |
| Semantic | chunker.py | Semantic boundaries | Partial |

### 5.3 Chunking Parameters
| Parameter | Value | Notes |
|---|---|---|
| Chunk Size | Configurable | Token-based |
| Overlap | Configurable | For context continuity |
| Min Chunk Size | Configurable | Prevent tiny chunks |
| Separators | Strategy-specific | Recursive: paragraphs, sentences |

---

## 6. Indexing Flow

### 6.1 Document Ingestion Pipeline
`mermaid
flowchart TD
    UPLOAD[File Upload] --> PARSE[Parse Document]
    PARSE --> CHUNK[Chunk Text]
    CHUNK --> EMBED[Generate Embeddings]
    EMBED --> INDEX[Index to Vector Store]
    INDEX --> UPDATE_BM25[Update BM25 Index]
    UPDATE_BM25 --> EXTRACT_ENTITIES[Extract Entities]
    EXTRACT_ENTITIES --> UPDATE_GRAPH[Update Knowledge Graph]
`

### 6.2 Document Parsers
| Format | Parser | Status |
|---|---|---|
| PDF | pdfplumber | Functional |
| DOCX | python-docx | Functional |
| LaTeX | Custom parser | Functional |
| TXT | Plain text | Functional |
| Markdown | markdown parser | Functional |

### 6.3 Indexing Strategies
| Strategy | Implementation | Status |
|---|---|---|
| Vector indexing | Qdrant/FAISS insert | Functional |
| BM25 indexing | Pickle serialization | Functional |
| Graph indexing | PostgreSQL ORM | Functional |
| Incremental | ? Missing | Full rebuild required |

---

## 7. Namespaces

### Current Implementation
| Namespace | Purpose | Isolation |
|---|---|---|
| documents | User-uploaded documents | Per-collection |
| knowledge | Knowledge base | Per-collection |
| Default | General embeddings | Shared |

### Assessment
| Aspect | Rating | Notes |
|---|---|---|
| Namespace isolation | Fair | Collection-based |
| Cross-namespace search | ? Missing | No federated search |
| Namespace management | Basic | Manual creation |
| Cleanup | ? Missing | No garbage collection |

---

## 8. Ranking System

### 8.1 Ranking Pipeline
`mermaid
flowchart LR
    CANDIDATES[Raw Candidates] --> DENSE_SCORE[Dense Score]
    CANDIDATES --> SPARSE_SCORE[Sparse Score]
    
    DENSE_SCORE --> RRF[RRF Fusion]
    SPARSE_SCORE --> RRF
    
    RRF --> RERANK[Cross-Encoder Rerank]
    RERANK --> FINAL[Final Ranking]
`

### 8.2 Ranking Factors
| Factor | Weight | Source |
|---|---|---|
| Dense similarity | Configurable | Vector search |
| BM25 score | Configurable | Sparse search |
| RRF fusion score | Calculated | Rank fusion |
| Cross-encoder score | Calculated | Reranking |
| Document freshness | ? Missing | N/A |
| Document authority | ? Missing | N/A |

---

## 9. Context Injection

### 9.1 Injection Strategy
`mermaid
flowchart TD
    RANKED[Ranked Chunks] --> DEDUP[Deduplication]
    DEDUP --> MERGE[Merge Adjacent]
    MERGE --> BUDGET[Token Budget Check]
    BUDGET --> TRUNCATE[Truncate if Needed]
    TRUNCATE --> FORMAT[Format Context]
    FORMAT --> INJECT[Inject into Prompt]
`

### 9.2 Injection Points
| Point | Method | Status |
|---|---|---|
| System prompt | Profile context | Functional |
| User message | Retrieved documents | Functional |
| Tool results | Execution context | Functional |
| Graph triples | Entity relationships | Partial |

### 9.3 Context Quality
| Aspect | Rating | Notes |
|---|---|---|
| Relevance | Good | Reranking helps |
| Diversity | Fair | Limited strategies |
| Completeness | Fair | May miss context |
| Freshness | Fair | No staleness detection |

---

## 10. Missing Enterprise Features

### Critical Missing
| Feature | Impact | Priority |
|---|---|---|
| Access Control | No document-level permissions | Critical |
| Audit Logging | No retrieval audit trail | Critical |
| Rate Limiting | Vulnerable to abuse | Critical |

### High-Priority Missing
| Feature | Impact | Priority |
|---|---|---|
| Incremental Indexing | Full rebuild for every change | High |
| Document Versioning | No change tracking | High |
| Multi-Tenancy | No tenant isolation | High |
| Query Analytics | No usage insights | High |
| Caching Layer | Repeated queries hit DB | High |

### Medium-Priority Missing
| Feature | Impact | Priority |
|---|---|---|
| Semantic Chunking | Better chunk quality | Medium |
| Hybrid Reranking | Combine multiple rerankers | Medium |
| Diversity Enforcement | Reduce redundancy | Medium |
| Citation Verification | Validate source accuracy | Medium |
| Document Freshness | Detect stale content | Medium |

---

## 11. Recommended Improvements

### Phase 1 (Critical)
| # | Improvement | Effort | Impact |
|---|---|---|---|
| 1 | Fix embedding dimension mismatch | Low | Prevents runtime errors |
| 2 | Add incremental BM25 indexing | Medium | Enables real-time updates |
| 3 | Add document-level access control | High | Enterprise requirement |

### Phase 2 (High Priority)
| # | Improvement | Effort | Impact |
|---|---|---|---|
| 4 | Add query analytics | Medium | Usage insights |
| 5 | Add Redis caching for queries | Medium | Performance improvement |
| 6 | Add document versioning | High | Change tracking |
| 7 | Improve BM25 tokenization | Low | Better keyword matching |

### Phase 3 (Medium Priority)
| # | Improvement | Effort | Impact |
|---|---|---|---|
| 8 | Add semantic chunking | Medium | Better chunk quality |
| 9 | Add diversity enforcement | Medium | Reduce redundancy |
| 10 | Add citation verification | High | Accuracy improvement |
| 11 | Add document freshness detection | Medium | Staleness prevention |

---

## 12. Performance Metrics

### Current Latency (Estimated)
| Stage | Latency | Notes |
|---|---|---|
| Query Processing | 100-300ms | LLM-based |
| Dense Search | 50-200ms | Qdrant query |
| BM25 Search | 10-50ms | In-memory |
| RRF Fusion | 5-10ms | CPU-bound |
| Reranking | 100-500ms | Cross-encoder |
| Compression | 10-30ms | CPU-bound |
| **Total Retrieval** | **300-1100ms** | End-to-end |

### Optimization Opportunities
| Opportunity | Expected Improvement |
|---|---|
| Query result caching | 50-80% latency reduction |
| Async embedding generation | 20-40% throughput increase |
| Batch processing | 30-50% throughput increase |
| Pre-computed embeddings | 90%+ latency reduction |

---

*This document was generated as part of the NORAY OS Phase 1 Technical Audit.*
