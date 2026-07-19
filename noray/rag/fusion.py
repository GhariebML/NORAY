from typing import List, Dict, Any, Optional

def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    sparse_results: List[Dict[str, Any]],
    k: int = 60,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Combines dense and sparse search results using Reciprocal Rank Fusion (RRF).
    
    Arguments:
        dense_results: List of hits: [{"id": str, "score": float, "payload": dict}]
        sparse_results: List of hits: [{"id": str, "score": float, "payload": dict}]
        k: RRF constant parameter (defaults to 60)
        limit: Max number of combined results to return
    """
    rrf_scores = {}
    payload_map = {}
    content_map = {}

    # Helper function to process hits from a retriever
    def process_hits(hits):
        for rank, hit in enumerate(hits, start=1):
            doc_id = hit["id"]
            payload_map[doc_id] = hit.get("payload", {})
            if "content" in hit:
                content_map[doc_id] = hit["content"]
            elif "content" in hit.get("payload", {}):
                content_map[doc_id] = hit["payload"]["content"]
                
            score = 1.0 / (k + rank)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + score

    # Process dense and sparse results
    process_hits(dense_results)
    process_hits(sparse_results)

    # Sort documents by RRF score descending
    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    # Build final outputs
    fused_results = []
    for doc_id, score in sorted_docs[:limit]:
        hit = {
            "id": doc_id,
            "score": score,
            "payload": payload_map[doc_id]
        }
        if doc_id in content_map:
            hit["content"] = content_map[doc_id]
        fused_results.append(hit)
        
    return fused_results
