import requests
import logging
from typing import Dict, Any, List, Optional
from academic_demo.components.config import API_BASE_URL

logger = logging.getLogger("academic_demo.api")

def get_health() -> Dict[str, Any]:
    """Check backend health."""
    try:
        res = requests.get(f"{API_BASE_URL}/api/health", timeout=3)
        if res.status_code == 200:
            return {"status": "healthy", "latency_ms": int(res.elapsed.total_seconds() * 1000)}
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
    return {"status": "offline", "latency_ms": 999}

def get_diagnostics() -> Dict[str, Any]:
    """Retrieve system-wide ingestion diagnostics."""
    try:
        res = requests.get(f"{API_BASE_URL}/api/system/ingestion-diagnostics", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        logger.warning(f"Ingestion diagnostics failed: {e}")
    
    # Try legacy endpoint fallback
    try:
        res = requests.get(f"{API_BASE_URL}/api/system/diagnostics", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
         logger.warning(f"Diagnostics backup failed: {e}")
    
    return {"status": "degraded", "error": "Unable to connect to diagnostics endpoint."}

def upload_file(file_content: bytes, filename: str, category: str = "general") -> Dict[str, Any]:
    """Upload document content directly to the backend."""
    try:
        files = {"file": (filename, file_content)}
        data = {"category": category}
        res = requests.post(f"{API_BASE_URL}/api/documents/upload", files=files, data=data, timeout=60)
        if res.status_code == 200:
            return res.json()
        else:
            return {"error": f"API Error {res.status_code}: {res.text}"}
    except Exception as e:
        return {"error": f"Upload request failed: {str(e)}"}

def list_documents() -> List[Dict[str, Any]]:
    """List indexed document library items."""
    try:
        res = requests.get(f"{API_BASE_URL}/api/documents/list", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        logger.warning(f"Listing documents failed: {e}")
    return []

def delete_document(point_id: str) -> bool:
    """Delete a document by its Qdrant point UUID."""
    try:
        res = requests.delete(f"{API_BASE_URL}/api/documents/{point_id}", timeout=10)
        return res.status_code == 200
    except Exception as e:
        logger.warning(f"Deleting document {point_id} failed: {e}")
        return False

def chat_workspace(query: str, session_id: str = "streamlit-session") -> Dict[str, Any]:
    """Execute query request via core workspace LLM/RAG pipeline with Demo Mode fallback."""
    try:
        payload = {"query": query, "session_id": session_id}
        res = requests.post(f"{API_BASE_URL}/api/workspace/chat", json=payload, timeout=90)
        if res.status_code == 200:
            return res.json()
        else:
            return {"response": f"API Error ({res.status_code}): {res.text}", "citations": [], "explainability": {}}
    except Exception as e:
        logger.warning(f"Backend unreachable ({e}). Activating Demo Mode response.")
        return {
            "intent": "Demo Mode (Offline Fallback)",
            "response": f"**[Demo Mode Active]** NORAY received your query: *\"{query}\"*\n\n"
                        f"The live backend API at `{API_BASE_URL}` is currently offline or unreachable. "
                        f"In live mode, NORAY fuses dense vector searches (Qdrant) with sparse keyword indices (BM25) "
                        f"and streams synthesized responses with full explainability traces.",
            "citations": [
                {"source": "Sample_Academic_Paper.pdf", "score": 0.9412},
                {"source": "Career_Profile_Summary.md", "score": 0.8875}
            ],
            "explainability": {
                "confidence_score": 0.95,
                "reasoning_steps": [
                    "Activated Streamlit Demo Mode fallback protocol.",
                    "Fused dense vector embedding matches from local Qdrant collection.",
                    "Reranked candidate chunks using Cross-Encoder model."
                ]
            }
        }
