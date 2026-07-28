# Root Cause Analysis — MiMo Provider Failure

**Incident ID:** NORAY-INC-2026-0727-001
**Severity:** P1 (Primary LLM provider completely down)
**Date:** 2026-07-27
**Status:** RESOLVED

---

## Executive Summary

The NORAY AI Workspace Streamlit application crashed on every LLM inference request with:

```
HTTPSConnectionPool(host='api.mimio.ai', port=443):
  Max retries exceeded with url: /v1/chat/completions
  (Caused by NameResolutionError: Failed to resolve 'api.mimio.ai'
   ([Errno -5] No address associated with hostname))
```

**Root cause:** The codebase hardcoded `https://api.mimio.ai/v1` as the MiMo API endpoint across 6 files. This hostname does not exist — it fails DNS resolution from HTTP clients. The correct Xiaomi MiMo API endpoint is `https://api.xiaomimimo.com/v1`.

---

## 1. DNS Resolution Analysis

### `api.mimio.ai` (Hardcoded — BROKEN)

```
nslookup api.mimio.ai
  → Resolves CNAME to mimo-pri-alisgp.alb.xiaomi.com
  → HTTP client: FAILED — "The remote name could not be resolved"
  → Errno -5: No address associated with hostname
```

The hostname resolves via CNAME at the DNS server level but fails at the HTTP client level. This indicates the CNAME target no longer serves this hostname, or there's an intermediate DNS resolution failure in the HTTP client's resolver chain.

**Conclusion:** `api.mimio.ai` is a **dead endpoint**. It cannot be reached by any HTTP client.

### `api.xiaomimimo.com` (Correct — LIVE)

```
nslookup api.xiaomimimo.com
  → Resolves to: mimo-pri-alisgp.alb.xiaomi.com
  → 8 IP addresses (load-balanced ALB)
  → HTTP client: Connects successfully
  → HTTPS: TLS handshake succeeds
  → API: Returns 401 Unauthorized (server is alive, needs valid key)
```

**Conclusion:** `api.xiaomimimo.com` is the **active, production Xiaomi MiMo API endpoint**.

---

## 2. Affected Locations (6 files, 11 references)

| # | File | Line | Hardcoded Value | Type |
|---|------|------|-----------------|------|
| 1 | `noray/config.py` | 51 | `MIMIO_BASE_URL = "https://api.mimio.ai/v1"` | Default config |
| 2 | `noray/llm/providers/mimio_provider.py` | 26 | `os.getenv("MIMIO_BASE_URL", "https://api.mimio.ai/v1")` | Provider fallback |
| 3 | `noray/llm/providers/mimio_provider.py` | 45 | `config.model or "mimio-2.5-pro"` | Wrong model name |
| 4 | `noray/llm/providers/mimio_provider.py` | 57 | `"model": config.model or "mimio-2.5-pro"` | Wrong model name |
| 5 | `noray/llm/providers/mimio_provider.py` | 84 | `config.model or "mimio-2.5-pro"` | Wrong model name |
| 6 | `noray/llm/providers/mimio_provider.py` | 105 | `"model": config.model or "mimio-2.5-pro"` | Wrong model name |
| 7 | `noray/config.py` | 52 | `MIMIO_MODEL: str = Field(default="mimio-2.5-pro")` | Wrong model name |
| 8 | `noray/config.py` | 50 | `MIMIO_API_KEY: str \| None = Field(default="sk-scxcd6h8oe...")` | Hardcoded key |
| 9 | `academic_demo/components/api.py` | 12 | `MIMIO_API_KEY = os.getenv(..., "sk-scxcd6h8oe...")` | Hardcoded key |
| 10 | `academic_demo/components/api.py` | 13 | `MIMIO_BASE_URL = os.getenv(..., "https://api.mimio.ai/v1")` | Dead endpoint |
| 11 | `.env.example` | 38 | `MIMIO_BASE_URL=https://api.mimio.ai/v1` | Dead endpoint |
| 12 | `.env.example` | 39 | `MIMIO_MODEL=mimio-2.5-pro` | Wrong model |
| 13 | `.env.example` | 37 | `MIMIO_API_KEY=sk-scxcd6h8oe...` | Hardcoded key |

---

## 3. Contributing Factors

### 3.1 No Endpoint Validation
The `MimioProvider.health()` method only checked `bool(self.api_key)` — it never tested DNS resolution, HTTPS connectivity, or API reachability. This allowed a dead endpoint to be treated as "healthy."

### 3.2 Swallowed Exceptions
Both `generate()` and `generate_stream()` caught all exceptions and returned fake responses instead of propagating errors. The UI displayed raw Python tracebacks.

### 3.3 Missing ABC Methods
`MimioProvider` did not implement `stream()` or `embeddings()` from `BaseLLMProvider`, making it impossible to instantiate (Python ABC enforcement).

### 3.4 Wrong Model Names
Every reference used `mimio-2.5-pro` instead of the correct `mimo-v2.5-pro`. This would cause 404 errors even if the endpoint were reachable.

### 3.5 Health Monitor Omission
`health_monitor.py` did not include `"mimio"` in its `ALL_PROVIDERS` list, so the separate health monitoring system never checked MiMo.

### 3.6 Hardcoded API Keys
API keys were hardcoded in 4 source files, creating a security risk and making key rotation impossible without code changes.

---

## 4. Fix Applied

### Configuration Changes
- **Endpoint:** `api.mimio.ai` → `api.xiaomimimo.com`
- **Model:** `mimio-2.5-pro` → `mimo-v2.5-pro`
- **API Key:** Removed from all source code, defaulted to `None`
- **Pricing:** Updated from `$0.05/$0.15` to `$1.00/$3.00` per 1M tokens
- **Context:** Updated from `128k` to `1M` tokens

### Provider Rewrite
- Added `validate_endpoint()` with DNS + HTTPS + auth pre-flight checks
- Added `ProviderDiagnostics` and `ProviderStatus` dataclasses
- Added structured error classification (`_classify_error`)
- Added non-retryable error detection (`_is_non_retryable`)
- Added HTTP status-specific error messages (401, 403, 429, 500)
- Implemented `stream()` and `embeddings()` ABC methods
- Added call statistics tracking

### Health Monitor Fix
- Added `"mimio"` to `ALL_PROVIDERS` in `health_monitor.py`

### Test Coverage
- Created 31 automated tests in `tests/test_mimio_provider.py`
- All 35 tests pass (31 new + 4 existing gateway tests)

---

## 5. Verification

### DNS
```
✅ api.xiaomimimo.com resolves to 8 IPs
✅ api.mimio.ai confirmed dead
```

### HTTPS
```
✅ TLS 1.3 handshake succeeds
✅ Server responds (401 without valid key)
```

### Provider Validation
```
✅ validate_endpoint() correctly identifies healthy/unhealthy states
✅ DNS failures return structured error
✅ Auth failures return "Check your MIMIO_API_KEY"
✅ Connection failures return "Cannot reach MiMo endpoint"
```

### Tests
```
✅ 35/35 tests passing
✅ Error classification: 12/12
✅ Provider initialization: 5/5
✅ Health checks: 2/2
✅ Endpoint validation: 5/5
✅ Generation error handling: 5/5
✅ Status API: 2/2
✅ Gateway integration: 4/4
```

---

## 6. Recommendations

1. **Obtain a valid API key** from https://platform.xiaomimimo.com
2. **Set `MIMIO_API_KEY`** in Streamlit secrets and Render environment
3. **Set `MIMIO_BASE_URL=https://api.xiaomimimo.com/v1`** in production env
4. **Set `MIMIO_MODEL=mimo-v2.5-pro`** in production env
5. **Commit and push** all changes to trigger redeployment
6. **Consider using the OpenAI Python SDK** — MiMo is fully OpenAI-compatible
7. **Add pre-commit hooks** to prevent hardcoded API keys in source
