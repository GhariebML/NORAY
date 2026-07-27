# System Fix & Refactoring Changelog

---

## 🛠️ Summary of Fixes Applied

1. **`noray/gateway/registry.py`**:
   - Re-ordered `ModelMetadata` priority values: Gemini (1), OpenRouter (2), Together (3), DeepSeek (4), Gemma Local (5), Qwen Coder Local (6).

2. **`noray/shared/vector_memory.py`**:
   - Refactored `VectorMemory` class to connect to `VectorStoreFactory` and removed 5 stub `TODO` comments.

3. **`noray/api/app.py` & `pyproject.toml` & `frontend/package.json`**:
   - Bumped system version strings to `1.0.0` for Release Candidate 1.

4. **`noray/api/routes/documents.py`**:
   - Stripped stack tracebacks from HTTP exception response bodies.

5. **`frontend/src/app/settings/page.tsx`**:
   - Restored `monthlyCost` and `tokenUsage` state declarations to resolve TypeScript compilation errors during Next.js production builds.

6. **Frontend Component Cleanups**:
   - Removed 133 unused imports across 21 TSX components to achieve **0 ESLint warnings**.
