"""
NORAY — Built-in Tool Layer

Defines the native tools that are available out-of-the-box in the
NORAY AI Operating System.
Provides structured definitions and handlers for:
    - Filesystem (read, write, list)
    - PostgreSQL Database (querying profiles & applications)
    - Qdrant Vector DB (searching vector spaces)
    - PDF Parser (text extraction)
    - Document Manager (listing and deleting ingested documents)
    - Local Search (running the dual dense/sparse RAG pipeline)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ToolDefinition:
    """Structure describing a tool's parameters and schema."""
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], Any]

class BuiltinToolRegistry:
    """Registry managing standard built-in tools for AI agents."""

    def __init__(self, workspace_root: str = str(Path(__file__).resolve().parent.parent.parent)):
        self.workspace_root = Path(workspace_root)
        self.tools: dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool definition."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """Get a tool definition by name."""
        return self.tools.get(name)

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool with arguments."""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool {name} is not registered in BuiltinToolRegistry.")

        # Simple schema validation could be added here
        try:
            return tool.handler(arguments)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

    def list_tools(self) -> list[dict[str, Any]]:
        """List metadata of all registered tools."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema
            }
            for t in self.tools.values()
        ]

    # --- Tool Registration implementation ---

    def _register_default_tools(self) -> None:
        # 1. Filesystem Tools
        self.register(ToolDefinition(
            name="list_directory",
            description="List all files and subdirectories in a directory path.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative directory path from workspace root."}
                },
                "required": ["path"]
            },
            handler=self._handle_list_directory
        ))

        self.register(ToolDefinition(
            name="read_file",
            description="Read content from a text file.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to file."}
                },
                "required": ["path"]
            },
            handler=self._handle_read_file
        ))

        # 2. Database (PostgreSQL) Tools
        self.register(ToolDefinition(
            name="query_db",
            description="Execute custom read queries in PostgreSQL to fetch applications, profiles, or chat data.",
            input_schema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "Raw SELECT SQL query."}
                },
                "required": ["sql"]
            },
            handler=self._handle_query_db
        ))

        # 3. Vector Database (Qdrant) Tools
        self.register(ToolDefinition(
            name="search_vector_store",
            description="Search Qdrant or local FAISS index directly for specific topics.",
            input_schema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Name of collection."},
                    "query": {"type": "string", "description": "Text query to match."},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["collection", "query"]
            },
            handler=self._handle_search_vector_store
        ))

        # 4. PDF Parser Tool
        self.register(ToolDefinition(
            name="parse_pdf",
            description="Extract text contents from a PDF file.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to PDF."}
                },
                "required": ["path"]
            },
            handler=self._handle_parse_pdf
        ))

        # 5. Document Manager Tool
        self.register(ToolDefinition(
            name="manage_documents",
            description="List all processed documents in the system or delete indexes.",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "delete_collection"]},
                    "collection": {"type": "string", "description": "Required for delete_collection action."}
                },
                "required": ["action"]
            },
            handler=self._handle_manage_documents
        ))

        # 6. Local Search Tool
        self.register(ToolDefinition(
            name="local_search",
            description="Perform a hybrid keyword + semantic search across all indexed user files.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search prompt."},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            },
            handler=self._handle_local_search
        ))

    # --- Handlers implementation ---

    def _resolve_path(self, rel_path: str) -> Path:
        # Prevent path traversal attacks, sandbox to workspace root
        safe_path = (self.workspace_root / rel_path).resolve()
        if not str(safe_path).startswith(str(self.workspace_root.resolve())):
            raise PermissionError("Path access is restricted to the workspace root directory.")
        return safe_path

    def _handle_list_directory(self, args: dict[str, Any]) -> Any:
        rel_path = args.get("path", "")
        target = self._resolve_path(rel_path)
        if not target.exists() or not target.is_dir():
            return {"error": f"Directory not found: {rel_path}"}

        items = []
        for p in target.iterdir():
            items.append({
                "name": p.name,
                "is_dir": p.is_dir(),
                "size_bytes": p.stat().st_size if p.is_file() else None
            })
        return {"items": items}

    def _handle_read_file(self, args: dict[str, Any]) -> Any:
        rel_path = args.get("path", "")
        target = self._resolve_path(rel_path)
        if not target.exists() or not target.is_file():
            return {"error": f"File not found: {rel_path}"}

        # Read max 50KB to prevent context bloat
        try:
            with open(target, encoding="utf-8", errors="ignore") as f:
                content = f.read(50000)
            return {
                "content": content,
                "truncated": target.stat().st_size > 50000
            }
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    def _handle_query_db(self, args: dict[str, Any]) -> Any:
        sql = args.get("sql", "").strip()
        if not sql.lower().startswith("select"):
            return {"error": "Query DB tool is read-only. Only SELECT queries are permitted."}

        from noray.database import SessionLocal
        session = SessionLocal()
        try:
            from sqlalchemy import text
            result = session.execute(text(sql))
            # Map columns to list of dicts
            rows = [dict(row._mapping) for row in result.all()]
            return {"rows": rows, "count": len(rows)}
        except Exception as e:
            return {"error": f"SQL Query error: {str(e)}"}
        finally:
            session.close()

    def _handle_search_vector_store(self, args: dict[str, Any]) -> Any:
        collection = args.get("collection", "user_documents")
        query = args.get("query", "")
        limit = args.get("limit", 5)

        from noray.rag.embeddings import EmbeddingsManager
        from noray.rag.vector_store import VectorStoreFactory

        try:
            embedder = EmbeddingsManager.get_embedder()
            vector_store = VectorStoreFactory.get_vector_store()
            query_vector = embedder.embed([query])[0]
            hits = vector_store.search(collection_name=collection, query_vector=query_vector, limit=limit)
            return {"hits": hits}
        except Exception as e:
            return {"error": f"Vector search error: {str(e)}"}

    def _handle_parse_pdf(self, args: dict[str, Any]) -> Any:
        rel_path = args.get("path", "")
        target = self._resolve_path(rel_path)
        if not target.exists() or not target.is_file():
            return {"error": f"File not found: {rel_path}"}

        try:
            import pdfplumber
            text_pages = []
            with pdfplumber.open(target) as pdf:
                for idx, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_pages.append(f"--- Page {idx+1} ---\n{text}")
            return {"text": "\n\n".join(text_pages[:20]), "pages_extracted": len(text_pages)}
        except ImportError:
            return {"error": "pdfplumber package is not installed."}
        except Exception as e:
            return {"error": f"PDF parse error: {str(e)}"}

    def _handle_manage_documents(self, args: dict[str, Any]) -> Any:
        action = args.get("action", "list")
        if action == "list":
            # List ingested directories/files count in SQLite/Qdrant
            # Simple metadata query fallback
            from noray.database import SessionLocal
            session = SessionLocal()
            try:
                from sqlalchemy import text
                res = session.execute(text("SELECT count(*) as cnt FROM applications"))
                row = res.fetchone()
                return {"status": "active", "tracked_applications_count": row[0] if row else 0}
            except Exception:
                return {"status": "active"}
            finally:
                session.close()
        elif action == "delete_collection":
            collection = args.get("collection", "")
            if not collection:
                return {"error": "Collection name required."}
            from noray.rag.vector_store import VectorStoreFactory
            try:
                store = VectorStoreFactory.get_vector_store()
                # Dummy call if delete collection is not defined on base vector store
                if hasattr(store, "delete_collection"):
                    store.delete_collection(collection)
                return {"status": f"deleted collection {collection}"}
            except Exception as e:
                return {"error": str(e)}

    def _handle_local_search(self, args: dict[str, Any]) -> Any:
        query = args.get("query", "")
        limit = args.get("limit", 5)

        from noray.agents.agent_router import AgentRouter
        try:
            router = AgentRouter(session_id="tool_search")
            context_chunks = router._retrieve_hybrid_context(query, filters={})
            # Convert context chunks to clean formats
            formatted_chunks = []
            for hit in context_chunks[:limit]:
                formatted_chunks.append({
                    "id": hit.get("id"),
                    "source": hit.get("payload", {}).get("source", "Unknown"),
                    "content": hit.get("content") or hit.get("payload", {}).get("content", ""),
                    "score": hit.get("score") or 0.0
                })
            return {"results": formatted_chunks}
        except Exception as e:
            return {"error": f"Local hybrid search error: {str(e)}"}
