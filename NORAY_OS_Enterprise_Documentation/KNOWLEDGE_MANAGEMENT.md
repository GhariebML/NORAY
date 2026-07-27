# Knowledge Management

## Global Knowledge Upload Center — ✅ Implemented

The **+ Add Knowledge** action is available globally across every workspace view. It supports:

- Document upload (PDF, DOCX, TXT, Markdown, CSV, XLSX, PPTX; images via an OCR path that is 🟡 under improvement)
- Automatic ingestion (validation → extraction → cleaning → chunking → embedding → indexing)
- Namespace selection, so knowledge can be scoped to a specific project, workspace, or context
- Document preview and management (viewing, removing indexed documents)

## Namespaces — ✅ Implemented

Every chunk is tagged with a namespace at ingestion time. Retrieval queries are namespace-aware, meaning the Universal Retriever only searches within the relevant scope rather than across all indexed knowledge indiscriminately. This underpins both the AI Workspace Canvas and the Notebook Workspace.

## Indexing — ✅ Implemented

Qdrant collections are created automatically at startup, keyed by namespace. Metadata (source document, chunk position, upload timestamp) is registered alongside each vector, making retrieved chunks traceable back to their origin — this is what powers the RAG Inspector panel's source citations.

## Document Lifecycle

```
Upload → Validate → Extract → Clean → Chunk → Embed → Store (Qdrant) → Register Metadata → Searchable
```

Once a document completes this pipeline, it is immediately searchable inside chat without requiring a manual re-index step.

## Current Limitations

- OCR for scanned/image-based documents is still being refined (🟡).
- Cross-namespace search / organization-wide knowledge bases are ⚪ planned, tied to the broader multi-tenant roadmap (see [`DEVELOPMENT_ROADMAP.md`](./DEVELOPMENT_ROADMAP.md)).
- Automatic re-chunking when a source document is updated is not yet implemented; re-uploading is currently required.
