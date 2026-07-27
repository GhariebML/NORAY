# Root Cause Analysis: Production vs Local Deployment

**Audit Date**: July 27, 2026  
**Lead Roles**: Principal DevOps Engineer & Site Reliability Engineer  
**Status**: ✅ **ANALYZED & STABILIZED**  

---

## 🔍 Root Cause Breakdown

### Issue 1: Next.js Production Build Failure (`monthlyCost` and `tokenUsage` State)
- **Root Cause**: Removal of unused state variables during ESLint cleanup broke JSX template bindings in `frontend/src/app/settings/page.tsx`.
- **Fix**: Re-declared `monthlyCost` and `tokenUsage` state with fallback default values.
- **Verification**: `npm run build` compiled 17/17 static pages with zero errors.

### Issue 2: Stack Traceback Exposure in Error Payloads
- **Root Cause**: FastAPI exception handlers in `noray/api/routes/documents.py` appended `traceback.format_exc()` to HTTP 500 error responses.
- **Fix**: Stripped traceback objects from exception payloads to prevent internal stack trace leakage.
- **Verification**: Error response bodies verified clean.

### Issue 3: Model Priority Mismatch in Gateway Router
- **Root Cause**: Hardcoded provider fallback expected OpenAI before Gemini.
- **Fix**: Re-ordered `ModelMetadata` priority values in `noray/gateway/registry.py` to prioritize Gemini (Priority 1).
- **Verification**: `pytest tests/test_ai_gateway.py` passed with 0 failures.

### Issue 4: Offline Ollama Status in Local Settings
- **Root Cause**: Local Ollama daemon was not running on local port 11434.
- **Fix**: System automatically falls back to Gemini Cloud LLM or memory vector store without throwing unhandled exceptions.
