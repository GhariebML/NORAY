# Defect Tracking & Bug Log: RC1 Audit

---

## 🐛 Discovered & Resolved Defects

### Bug 001: Missing Model Priority Mapping in AI Gateway Fallback Test
- **Severity**: Major (P2)
- **Component**: `noray/gateway/registry.py` / `tests/test_ai_gateway.py`
- **Description**: Updating Gemini to Priority 1 created an assertion mismatch in `test_model_router_fallback` which expected OpenAI as fallback.
- **Resolution**: Updated `test_model_router_fallback` assertion to validate Gemini as Priority 1 cloud provider.

### Bug 002: Stale TODO Comments in Vector Memory Stub
- **Severity**: Minor (P3)
- **Component**: `noray/shared/vector_memory.py`
- **Description**: File contained 5 unused `TODO` comments from early development.
- **Resolution**: Refactored `VectorMemory` to delegate directly to `VectorStoreFactory` and removed all `TODO` comments.

### Bug 003: Unused React Imports Triggering ESLint Warnings
- **Severity**: Minor (P3)
- **Component**: Frontend components across `src/app/` and `src/components/`
- **Description**: 133 unused Lucide icons and state variables triggered ESLint warnings.
- **Resolution**: Cleaned up all unused imports across 21 frontend files resulting in **0 ESLint warnings**.

### Bug 004: HTTP Error Response Traceback Exposure
- **Severity**: Security (P2)
- **Component**: `noray/api/routes/documents.py`
- **Description**: `list_documents` and `delete_document` routes included Python stack tracebacks in 500 error bodies.
- **Resolution**: Stripped traceback payloads from HTTP responses to prevent internal stack trace leakage.
