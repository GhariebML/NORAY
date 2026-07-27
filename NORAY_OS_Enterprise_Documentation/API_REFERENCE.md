# API Reference

> The endpoints below are **representative** of NORAY OS's FastAPI backend structure. They illustrate the shape of the API rather than serving as an exhaustive, versioned specification. Refer to the auto-generated OpenAPI docs (`/docs`, served by FastAPI) in the running instance for the authoritative, current contract.

## Base URL

```
http://localhost:8000/api/v1
```

## Chat / Workspace

### `POST /chat/message`

Send a message to the AI Workspace.

**Request**
```json
{
  "session_id": "string",
  "message": "string",
  "namespace": "string (optional)"
}
```

**Response** (streamed)
```json
{
  "type": "text | tool_use | citation",
  "content": "string",
  "sources": [ { "document": "string", "score": 0.0 } ]
}
```

## Knowledge / Ingestion

### `POST /knowledge/upload`

Uploads and ingests a document.

**Request:** multipart/form-data — `file`, `namespace`

**Response**
```json
{
  "document_id": "string",
  "status": "processing | indexed | failed",
  "chunks_created": 0
}
```

### `GET /knowledge/documents`

Lists indexed documents for the current namespace.

## Retrieval

### `POST /retrieve/context`

Runs the Universal Retriever directly (used internally by chat, exposed for debugging/inspection).

**Request**
```json
{ "query": "string", "namespace": "string", "top_k": 10 }
```

**Response**
```json
{
  "results": [
    { "content": "string", "source": "string", "score": 0.0, "retrieval_method": "dense | bm25 | metadata" }
  ]
}
```

## Document Generation

### `POST /documents/generate`

**Request**
```json
{
  "type": "cv | sop | motivation_letter | research_proposal",
  "target_company": "string (optional)",
  "target_role": "string (optional)",
  "job_url": "string (optional)"
}
```

**Response**
```json
{ "document_url": "string", "format": "docx" }
```

## Telemetry

### `GET /telemetry/summary`

Returns aggregate token usage, cost, and latency metrics.

## Diagnostics

### `GET /diagnostics/health`

Returns health status for the database, Qdrant, Ollama, and configured cloud providers.

---

## Authentication

⚪ **Planned.** All endpoints above are currently unauthenticated, consistent with NORAY OS's local-first, single-user design. Once authentication is introduced (JWT/OAuth — see [`DEVELOPMENT_ROADMAP.md`](./DEVELOPMENT_ROADMAP.md)), this document will be updated with the required headers and token flow.
