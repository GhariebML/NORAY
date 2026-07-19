import re
from typing import List, Dict, Any, Optional
from noray.shared.llm_utils import call_llm, LLMConfig

class QueryProcessor:
    """Handles query understanding: intent classification, query expansion, HyDE document generation, and filter extraction."""
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm

    def classify_intent(self, query: str) -> str:
        """Classifies user query intent: career, scholarship, documents, or general."""
        query_lower = query.lower()
        
        # Simple rule-based classification as primary/fallback
        if any(w in query_lower for w in ["job", "vacancy", "career", "salary", "interview", "hiring", "company", "cv", "resume", "ats"]):
            return "career"
        elif any(w in query_lower for w in ["scholarship", "daad", "chevening", "fulbright", "erasmus", "fellowship", "sop", "proposal", "phd", "master", "funding"]):
            return "scholarship"
        elif any(w in query_lower for w in ["document", "upload", "ingest", "file", "pdf", "docx", "markdown", "index", "knowledge"]):
            return "documents"
        
        if not self.use_llm:
            return "general"

        # Try LLM classification
        try:
            prompt = (
                f"Classify the following query into one of these intents: 'career', 'scholarship', 'documents', 'general'.\n"
                f"Query: \"{query}\"\n"
                f"Respond with ONLY the class name in lowercase."
            )
            resp = call_llm(prompt, LLMConfig(temperature=0.0, max_tokens=10))
            intent = resp.content.strip().lower()
            if intent in ["career", "scholarship", "documents", "general"]:
                return intent
        except Exception:
            pass
        
        return "general"

    def expand_query(self, query: str, num_queries: int = 3) -> List[str]:
        """Generates alternative phrasings of the input query to improve retrieval recall."""
        queries = [query]
        if not self.use_llm:
            return queries

        try:
            prompt = (
                f"Generate {num_queries} alternative search queries to retrieve documents related to the following query.\n"
                f"Query: \"{query}\"\n"
                f"Write one query per line. Do not number them or include other text."
            )
            resp = call_llm(prompt, LLMConfig(temperature=0.6, max_tokens=200))
            lines = resp.content.split("\n")
            for line in lines:
                cleaned = line.strip().strip('"').strip("'")
                if cleaned and len(cleaned) > 5:
                    queries.append(cleaned)
        except Exception:
            pass
            
        return list(set(queries))[:num_queries + 1]

    def generate_hyde_doc(self, query: str) -> str:
        """Generates a hypothetical document containing an answer to the query (Hypothetical Document Embedding)."""
        if not self.use_llm:
            return query

        try:
            prompt = (
                f"Write a short paragraph answering the following query. Write as if you are a textbook or standard reference guide.\n"
                f"Query: \"{query}\"\n"
                f"Paragraph:"
            )
            resp = call_llm(prompt, LLMConfig(temperature=0.3, max_tokens=300))
            return resp.content.strip()
        except Exception:
            return query

    def extract_metadata_filters(self, query: str) -> Dict[str, Any]:
        """Extracts known filter fields from the query text (e.g. countries, degrees)."""
        filters = {}
        query_lower = query.lower()

        # Simple pattern matching for countries
        countries = {
            "germany": "Germany", "deutschland": "Germany",
            "uk": "United Kingdom", "united kingdom": "United Kingdom", "britain": "United Kingdom",
            "us": "United States", "usa": "United States", "united states": "United States",
            "denmark": "Denmark", "danmark": "Denmark",
            "uae": "UAE", "emirates": "UAE"
        }
        for kw, country in countries.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", query_lower):
                filters["country"] = country
                break

        # Simple pattern matching for degrees
        degrees = {
            "phd": "PhD", "doctorate": "PhD", "postdoc": "PostDoc",
            "master": "MSc", "msc": "MSc", "ma": "MSc",
            "bachelor": "BSc", "bsc": "BSc", "ba": "BSc"
        }
        for kw, degree in degrees.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", query_lower):
                filters["degree"] = degree
                break

        # Check for active status
        if "old" in query_lower or "outdated" in query_lower or "archive" in query_lower:
            filters["is_current"] = False
        elif "current" in query_lower or "active" in query_lower or "latest" in query_lower:
            filters["is_current"] = True

        return filters
