"""
NORAY — Graceful Retrieval Pipeline

Implements a resilient, multi-stage retrieval pipeline where every step is optional.
Failure of any step never terminates execution — the system gracefully degrades
through a fallback chain: Dense Vector → BM25 → Metadata → Conversation Memory → LLM Only.

Each stage logs structured telemetry for diagnostics (never visible to users).
"""

from __future__ import annotations

import logging
import time
from typing import Any

from noray.rag.compressor import ContextCompressor
from noray.rag.embeddings import EmbeddingsManager
from noray.rag.fusion import reciprocal_rank_fusion
from noray.rag.memory import ChatMemoryManager, ProfileMemoryManager
from noray.rag.query_processor import QueryProcessor
from noray.rag.reranker import RerankerManager
from noray.rag.sparse_index import SparseBM25Index
from noray.rag.telemetry import PipelineStepTelemetry, PipelineTimer, RetrievalTelemetry, telemetry_store
from noray.rag.vector_store import VectorStoreFactory
from noray.shared.profile_store import load_profile

logger = logging.getLogger("noray.rag.pipeline")

# User-facing messages that replace internal errors
_USER_FACING_MESSAGES = {
    "collection_missing": "Knowledge base is still being prepared.",
    "vector_search_failed": "Searching available knowledge...",
    "bm25_failed": "Using alternative retrieval strategy.",
    "metadata_failed": "Optimizing response generation.",
    "reranker_failed": "Processing available information.",
    "all_retrieval_failed": "Knowledge source unavailable. Generating answer using conversation context.",
    "graph_failed": "Building response from available data.",
}

COLLECTION_NAME = "user_documents"


class RetrievalPipeline:
    """
    Resilient retrieval pipeline with full fallback chain.
    
    Order of operations:
        1. Dense Vector Search (Qdrant)
        2. BM25 Sparse Search
        3. Metadata Filtering
        4. Reranking (Cross-Encoder)
        5. Context Compression
        6. Conversation Memory Fallback
        7. LLM-Only Fallback
        
    Every step is optional. Failure never terminates execution.
    """

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.query_processor = QueryProcessor(use_llm=False)
        self.vector_store = VectorStoreFactory.get_vector_store()
        self.embedder = EmbeddingsManager.get_embedder()
        self.sparse_index = SparseBM25Index()
        self.reranker = RerankerManager.get_reranker()
        self.compressor = ContextCompressor(min_score_threshold=0.0)
        self.memory = ChatMemoryManager(session_id)

    def retrieve(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        session_id: str = "",
    ) -> dict[str, Any]:
        """
        Execute the full retrieval pipeline with graceful fallback.
        
        Returns dict with:
            - context: str (combined context text)
            - citations: list
            - chunks: list of raw chunks
            - telemetry: RetrievalTelemetry
            - fallback_chain: list of steps used
            - user_notice: str (user-facing message if degradation occurred)
        """
        telemetry = RetrievalTelemetry(
            query=query,
            session_id=session_id or self.session_id,
        )
        start_total = time.time()

        filters = filters or {}
        intent = self.query_processor.classify_intent(query)
        telemetry.intent = intent

        expanded_queries = self.query_processor.expand_query(query, num_queries=2)
        fallback_chain = []
        user_notice = ""
        all_chunks: list[dict[str, Any]] = []

        # ── Step 1: Dense Vector Search ──
        dense_results = self._try_dense_search(expanded_queries, filters, telemetry)
        all_chunks.extend(dense_results)

        if dense_results:
            fallback_chain.append("dense_vector")
        else:
            fallback_chain.append("dense_vector(fallback)")

        # ── Step 2: BM25 Sparse Search ──
        if not self._has_enough_results(all_chunks):
            bm25_results = self._try_bm25_search(expanded_queries, filters, telemetry)
            all_chunks.extend(bm25_results)
            if bm25_results:
                fallback_chain.append("bm25")
                if not dense_results:
                    user_notice = _USER_FACING_MESSAGES["bm25_failed"]
            else:
                fallback_chain.append("bm25(fallback)")

        # ── Step 3: RRF Fusion ──
        all_chunks = self._deduplicate_chunks(all_chunks)

        # ── Step 4: Reranking ──
        reranked = self._try_rerank(query, all_chunks, telemetry)
        if reranked:
            all_chunks = reranked
            fallback_chain.append("reranker")
        else:
            fallback_chain.append("reranker(skip)")

        # ── Step 5: Context Compression ──
        compressed = self._try_compress(query, all_chunks, telemetry)
        if compressed:
            all_chunks = compressed

        # ── Step 6: Conversation Memory Fallback ──
        conversation_context = ""
        if not all_chunks:
            conversation_context = self._try_conversation_memory(telemetry)
            if conversation_context:
                fallback_chain.append("conversation_memory")
                user_notice = _USER_FACING_MESSAGES["all_retrieval_failed"]
            else:
                fallback_chain.append("conversation_memory(empty)")
                user_notice = "No prior conversation found. Generating fresh response."

        # ── Build final context ──
        context_texts = []
        citations = []
        for idx, chunk in enumerate(all_chunks):
            content = chunk.get("content") or chunk.get("payload", {}).get("content", "")
            source = chunk.get("payload", {}).get("source", "Knowledge Base")
            score = chunk.get("rerank_score") or chunk.get("score") or 0.0
            citations.append({
                "id": chunk.get("id"),
                "source": source,
                "score": score,
            })
            context_texts.append(f"[Source: {source} (Result {idx+1})]\n{content}")

        context_block = "\n\n".join(context_texts)
        if conversation_context:
            if context_block:
                context_block += "\n\n" + conversation_context
            else:
                context_block = conversation_context

        telemetry.total_duration_ms = (time.time() - start_total) * 1000
        telemetry.fallback_chain_used = fallback_chain
        telemetry.final_status = "degraded" if fallback_chain and "fallback" in str(fallback_chain) else "success"

        telemetry_store.append(telemetry)

        return {
            "context": context_block,
            "citations": citations,
            "chunks": all_chunks,
            "telemetry": telemetry,
            "fallback_chain": fallback_chain,
            "user_notice": user_notice,
            "intent": intent,
        }

    def _try_dense_search(
        self, queries: list[str], filters: dict[str, Any], telemetry: RetrievalTelemetry
    ) -> list[dict[str, Any]]:
        """Attempt dense vector search. Returns empty list on failure."""
        step = PipelineStepTelemetry(step_name="dense_vector", embedding_model=self.embedder.model_name)
        start = time.time()

        try:
            # Validate Qdrant collection exists
            if not self._collection_exists():
                logger.warning(f"Collection '{COLLECTION_NAME}' does not exist — skipping vector search")
                step.error = f"Collection '{COLLECTION_NAME}' not found"
                step.recovery_action = "skipped"
                step.success = True
                step.latency_ms = (time.time() - start) * 1000
                telemetry.steps.append(step)
                return []

            results = []
            for q in queries:
                q_vec = self.embedder.embed([q])[0]
                hits = self.vector_store.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=q_vec,
                    limit=10,
                    filters=filters,
                )
                results.extend(hits)

            step.success = True
            step.retrieved_chunks = len(results)
            step.collection = COLLECTION_NAME
            step.latency_ms = (time.time() - start) * 1000
            if results:
                step.similarity_score = max(h.get("score", 0) for h in results)

            logger.info(f"Dense search: {len(results)} chunks, collection='{COLLECTION_NAME}'")
            telemetry.steps.append(step)
            return results

        except Exception as e:
            step.success = False
            step.error = str(e)
            step.recovery_action = "fallback_to_bm25"
            step.latency_ms = (time.time() - start) * 1000
            step.fallback_used = True
            logger.warning(f"Dense vector search failed: {e}")
            telemetry.steps.append(step)
            return []

    def _try_bm25_search(
        self, queries: list[str], filters: dict[str, Any], telemetry: RetrievalTelemetry
    ) -> list[dict[str, Any]]:
        """Attempt BM25 sparse search. Returns empty list on failure."""
        step = PipelineStepTelemetry(step_name="bm25")
        start = time.time()

        try:
            results = []
            for q in queries:
                hits = self.sparse_index.search(query=q, limit=10, filters=filters)
                results.extend(hits)

            step.success = True
            step.retrieved_chunks = len(results)
            step.latency_ms = (time.time() - start) * 1000
            if results:
                step.similarity_score = max(h.get("score", 0) for h in results)

            logger.info(f"BM25 search: {len(results)} chunks")
            telemetry.steps.append(step)
            return results

        except Exception as e:
            step.success = False
            step.error = str(e)
            step.recovery_action = "fallback_to_conversation_memory"
            step.fallback_used = True
            step.latency_ms = (time.time() - start) * 1000
            logger.warning(f"BM25 search failed: {e}")
            telemetry.steps.append(step)
            return []

    def _try_rerank(
        self, query: str, chunks: list[dict[str, Any]], telemetry: RetrievalTelemetry
    ) -> list[dict[str, Any]]:
        """Attempt cross-encoder reranking. Returns empty list on failure."""
        if not chunks:
            return []

        step = PipelineStepTelemetry(step_name="reranker")
        start = time.time()

        try:
            reranked = self.reranker.rerank(query=query, documents=chunks, top_k=5)
            step.success = True
            step.retrieved_chunks = len(reranked)
            step.latency_ms = (time.time() - start) * 1000
            telemetry.steps.append(step)
            return reranked
        except Exception as e:
            step.success = False
            step.error = str(e)
            step.recovery_action = "use_unranked_chunks"
            step.fallback_used = True
            step.latency_ms = (time.time() - start) * 1000
            logger.warning(f"Reranker failed, using unranked chunks: {e}")
            telemetry.steps.append(step)
            return chunks[:5]

    def _try_compress(
        self, query: str, chunks: list[dict[str, Any]], telemetry: RetrievalTelemetry
    ) -> list[dict[str, Any]]:
        """Attempt context compression. Returns empty list on failure."""
        if not chunks:
            return []

        step = PipelineStepTelemetry(step_name="compressor")
        start = time.time()

        try:
            compressed = self.compressor.clean_and_compress(chunks, query=query)
            step.success = True
            step.retrieved_chunks = len(compressed)
            step.latency_ms = (time.time() - start) * 1000
            telemetry.steps.append(step)
            return compressed
        except Exception as e:
            step.success = False
            step.error = str(e)
            step.recovery_action = "use_uncompressed_chunks"
            step.latency_ms = (time.time() - start) * 1000
            logger.warning(f"Compressor failed, using uncompressed chunks: {e}")
            telemetry.steps.append(step)
            return chunks

    def _try_conversation_memory(self, telemetry: RetrievalTelemetry) -> str:
        """Attempt to retrieve conversation history as fallback context."""
        step = PipelineStepTelemetry(step_name="conversation_memory")
        start = time.time()

        try:
            messages = self.memory.get_recent_messages(limit=5)
            if messages:
                context = "## Prior Conversation\n"
                for m in messages:
                    context += f"{m['role'].upper()}: {m['content']}\n"
                step.success = True
                step.retrieved_chunks = len(messages)
                step.latency_ms = (time.time() - start) * 1000
                logger.info(f"Conversation memory fallback: {len(messages)} messages")
                telemetry.steps.append(step)
                return context

            step.success = True
            step.retrieved_chunks = 0
            step.recovery_action = "llm_only"
            step.latency_ms = (time.time() - start) * 1000
            telemetry.steps.append(step)
            return ""

        except Exception as e:
            step.success = False
            step.error = str(e)
            step.recovery_action = "llm_only"
            step.latency_ms = (time.time() - start) * 1000
            logger.warning(f"Conversation memory fallback failed: {e}")
            telemetry.steps.append(step)
            return ""

    def _collection_exists(self) -> bool:
        """Check if the Qdrant collection exists."""
        try:
            self.vector_store._lazy_init()
            if hasattr(self.vector_store, "client") and self.vector_store.client:
                collections = self.vector_store.client.get_collections()
                return any(c.name == COLLECTION_NAME for c in collections.collections)
            if hasattr(self.vector_store, "indexes"):
                return COLLECTION_NAME in self.vector_store.indexes
            return False
        except Exception:
            return False

    def _has_enough_results(self, chunks: list[dict[str, Any]], threshold: int = 3) -> bool:
        """Check if we have sufficient results to proceed."""
        return len(chunks) >= threshold

    def _deduplicate_chunks(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate chunks by ID."""
        seen = set()
        deduped = []
        for c in chunks:
            cid = c.get("id")
            if cid and cid not in seen:
                seen.add(cid)
                deduped.append(c)
            elif not cid:
                deduped.append(c)
        return deduped


def build_pipeline_context(
    query: str,
    session_id: str,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Convenience function to run the full retrieval pipeline.
    Returns context dict suitable for LLM prompt building.
    """
    pipeline = RetrievalPipeline(session_id=session_id)
    result = pipeline.retrieve(query, filters=filters)

    # Attach profile memory
    try:
        profile_data = load_profile()
        profile_memory = ProfileMemoryManager(profile_data.model_dump())
        persona_prefix = profile_memory.get_profile_summary_prompt()
        result["persona"] = persona_prefix
    except Exception:
        result["persona"] = ""

    return result
