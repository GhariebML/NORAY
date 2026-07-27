from typing import Any

from noray.rag.compressor import ContextCompressor
from noray.rag.embeddings import EmbeddingsManager
from noray.rag.fusion import reciprocal_rank_fusion
from noray.rag.memory import ChatMemoryManager, ProfileMemoryManager
from noray.rag.query_processor import QueryProcessor
from noray.rag.reranker import RerankerManager
from noray.rag.sparse_index import SparseBM25Index
from noray.rag.vector_store import VectorStoreFactory
from noray.shared.profile_store import load_profile


class AgentRouter:
    """Orchestrates query classification, hybrid retrieval, context compression, and routes execution to appropriate agents."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.query_processor = QueryProcessor(use_llm=False)
        self.vector_store = VectorStoreFactory.get_vector_store()
        self.embedder = EmbeddingsManager.get_embedder()
        self.sparse_index = SparseBM25Index()
        self.reranker = RerankerManager.get_reranker()
        self.compressor = ContextCompressor(min_score_threshold=0.0)
        self.memory = ChatMemoryManager(session_id)

    def process_and_route(self, query: str) -> dict[str, Any]:
        """Runs RAG retrieval and routes to domain specific generators."""
        # 1. Intent Detection
        intent = self.query_processor.classify_intent(query)

        # 2. Extract Metadata Filters
        filters = self.query_processor.extract_metadata_filters(query)

        # 3. Retrieve Context via Hybrid search
        context_chunks = self._retrieve_hybrid_context(query, filters)

        # 4. Format context text block and citations list
        citations = []
        context_texts = []
        for idx, chunk in enumerate(context_chunks):
            content = chunk.get("content") or chunk.get("payload", {}).get("content", "")
            source = chunk.get("payload", {}).get("source", "Unknown")
            citations.append({
                "id": chunk.get("id"),
                "source": source,
                "score": chunk.get("rerank_score") or chunk.get("score") or 0.0
            })
            context_texts.append(f"[Source: {source} (Result {idx+1})]\n{content}")

        context_block = "\n\n".join(context_texts)

        # 5. Inject Short term history & User facts
        chat_history = self.memory.get_recent_messages(limit=5)
        profile_data = load_profile()
        profile_memory = ProfileMemoryManager(profile_data.model_dump())
        persona_prefix = profile_memory.get_profile_summary_prompt()

        # 6. Execute domain-specific logic or default general RAG chat
        response_text = self._dispatch_to_agent(
            intent=intent,
            query=query,
            context=context_block,
            persona=persona_prefix,
            history=chat_history
        )

        # 7. Save conversation message
        self.memory.add_message(role="user", content=query)
        self.memory.add_message(role="assistant", content=response_text, citations=citations)

        return {
            "intent": intent,
            "response": response_text,
            "citations": citations
        }

    def _retrieve_hybrid_context(self, query: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Retrieves passages using dense (Qdrant) + sparse (BM25) search fused with RRF and re-ranked."""
        # Query Expansion
        expanded_queries = self.query_processor.expand_query(query, num_queries=2)

        dense_results = []
        sparse_results = []

        # Run retrievals for each expanded query variation
        for q in expanded_queries:
            # Dense Vector Search
            try:
                q_vec = self.embedder.embed([q])[0]
                dense_hits = self.vector_store.search(
                    collection_name="user_documents",
                    query_vector=q_vec,
                    limit=10,
                    filters=filters
                )
                dense_results.extend(dense_hits)
            except Exception:
                pass

            # Sparse Lexical Search
            try:
                sparse_hits = self.sparse_index.search(query=q, limit=10, filters=filters)
                sparse_results.extend(sparse_hits)
            except Exception:
                pass

        # Fuse rankings using Reciprocal Rank Fusion (RRF)
        fused = reciprocal_rank_fusion(dense_results, sparse_results, limit=15)

        # Re-rank fused candidates using Cross-Encoder
        try:
            reranked = self.reranker.rerank(query=query, documents=fused, top_k=5)
        except Exception:
            reranked = fused[:5]

        # Context Compression & Merge adjacent chunks
        compressed = self.compressor.clean_and_compress(reranked, query=query)
        return compressed

    def _dispatch_to_agent(self, intent: str, query: str, context: str, persona: str, history: list[dict[str, str]]) -> str:
        """Invokes LLM with customized system prompts based on target agent intent."""
        from noray.shared.llm_utils import LLMConfig, call_llm

        # Build history text
        history_text = ""
        for h in history:
            history_text += f"{h['role'].upper()}: {h['content']}\n"

        system_base = (
            f"You are the NORAY Platform AI. Use the supplied grounded Knowledge Context to answer the query.\n"
            f"Adhere strictly to the facts present in the Context. If the answer cannot be found in the context, "
            f"politely state that the information is missing. Always cite sources at the end of statements where they apply.\n\n"
            f"User Profile Persona:\n{persona}\n\n"
            f"Knowledge Context:\n{context}\n"
        )

        if intent == "career":
            system_prompt = (
                f"{system_base}\n"
                f"Domain: Career Advisory & Resume Tailoring Agent.\n"
                f"Help the user optimize their resume, tailor applications, evaluate fit, or practice for interviews."
            )
        elif intent == "scholarship":
            system_prompt = (
                f"{system_base}\n"
                f"Domain: Academic Scholarships & Grants Advisor.\n"
                f"Focus on eligibility requirements, program deadlines, research proposals, or Statement of Purpose outlines."
            )
        else:
            system_prompt = (
                f"{system_base}\n"
                f"Domain: General Knowledge Workspace Assistant."
            )

        prompt = f"Recent History:\n{history_text}\nUser Query: {query}\nResponse:"

        try:
            resp = call_llm(prompt, LLMConfig(temperature=0.3, max_tokens=1500, system_prompt=system_prompt))
            return resp.content
        except Exception as e:
            return f"Error invoking agent LLM planner: {e}"
