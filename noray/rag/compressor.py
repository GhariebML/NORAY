from typing import Any


class ContextCompressor:
    """Optimizes and compresses context before sending it to the LLM."""
    def __init__(self, min_score_threshold: float = 0.0):
        self.min_score_threshold = min_score_threshold

    def clean_and_compress(self, hits: list[dict[str, Any]], query: str = None) -> list[dict[str, Any]]:
        """
        Deduplicates hits, filters by score threshold, and merges overlapping adjacent chunks.
        """
        if not hits:
            return []

        # Step 1: Filter by score threshold (if score is available)
        filtered_hits = []
        for hit in hits:
            # RRF or rerank score
            score = hit.get("rerank_score") or hit.get("score") or 0.0
            if score >= self.min_score_threshold:
                filtered_hits.append(hit)

        if not filtered_hits:
            return []

        # Step 2: Deduplicate by content (or metadata id)
        seen_texts = set()
        seen_ids = set()
        deduped_hits = []

        for hit in filtered_hits:
            doc_id = hit.get("id")
            text = hit.get("content") or hit.get("payload", {}).get("content", "").strip()

            if not text:
                continue

            # Standardize text for dedup check
            norm_text = " ".join(text.lower().split())

            if doc_id in seen_ids or norm_text in seen_texts:
                continue

            seen_ids.add(doc_id)
            seen_texts.add(norm_text)
            deduped_hits.append(hit)

        # Step 3: Merge overlapping consecutive chunks from the same document
        # Map hits by source document
        merged_hits = []
        document_chunks = {}

        for hit in deduped_hits:
            payload = hit.get("payload", {})
            source = payload.get("source") or payload.get("filename") or "unknown_source"
            chunk_idx = payload.get("chunk_index")

            if source == "unknown_source" or chunk_idx is None:
                # Can't merge if metadata is missing, add directly
                merged_hits.append(hit)
                continue

            if source not in document_chunks:
                document_chunks[source] = []
            document_chunks[source].append(hit)

        # Sort chunks inside each document by chunk_index and merge if consecutive
        for source, chunks in document_chunks.items():
            # Sort by chunk_index ascending
            sorted_chunks = sorted(chunks, key=lambda x: x.get("payload", {}).get("chunk_index", 0))

            merged_docs = []
            current_merged = sorted_chunks[0].copy()

            for next_chunk in sorted_chunks[1:]:
                curr_idx = current_merged.get("payload", {}).get("chunk_index", 0)
                next_idx = next_chunk.get("payload", {}).get("chunk_index", 0)

                # If they are adjacent (differ by 1), merge them
                if next_idx == curr_idx + 1:
                    curr_text = current_merged.get("content") or current_merged.get("payload", {}).get("content", "")
                    next_text = next_chunk.get("content") or next_chunk.get("payload", {}).get("content", "")

                    # Deduplicate overlap at boundary if overlap exists
                    # (Simple suffix-prefix overlap strip or just stitch with space)
                    stitched_text = self._stitch_with_overlap(curr_text, next_text)

                    current_merged["content"] = stitched_text
                    if "payload" in current_merged:
                        current_merged["payload"]["content"] = stitched_text
                        current_merged["payload"]["chunk_index"] = next_idx # advance index
                else:
                    merged_docs.append(current_merged)
                    current_merged = next_chunk.copy()

            merged_docs.append(current_merged)
            merged_hits.extend(merged_docs)

        # Final re-sort of merged hits by score descending
        merged_hits = sorted(
            merged_hits,
            key=lambda x: x.get("rerank_score") or x.get("score") or 0.0,
            reverse=True
        )
        return merged_hits

    def _stitch_with_overlap(self, text1: str, text2: str) -> str:
        """Stitches text1 and text2, attempting to deduplicate common boundary words."""
        words1 = text1.split()
        words2 = text2.split()

        max_overlap = min(len(words1), len(words2), 30) # check up to 30 words overlap
        best_overlap_size = 0

        for size in range(1, max_overlap + 1):
            suffix = words1[-size:]
            prefix = words2[:size]
            if suffix == prefix:
                best_overlap_size = size

        if best_overlap_size > 0:
            # Stitch excluding prefix duplication in text2
            merged_words = words1 + words2[best_overlap_size:]
            return " ".join(merged_words)

        return text1 + " " + text2
