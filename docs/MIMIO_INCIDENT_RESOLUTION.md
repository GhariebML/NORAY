# NORAY OS — Mimio Provider Incident Resolution Report

**Date:** July 2026
**Severity:** Critical ? Resolved
**Status:** ? RESOLVED

---

## 1. Executive Summary

The Xiaomi MiMo provider integration was completely non-functional due to a **dead DNS endpoint** (pi.mimio.ai). The hostname does not resolve from HTTP clients, causing every inference request to fail with NameResolutionError.

**Root Cause:** The API endpoint https://api.mimio.ai/v1 was hardcoded across 6+ files. This hostname does not exist.

**Resolution:** All references updated to the correct endpoint https://api.xiaomimimo.com/v1.

---

## 2. Timeline

| Time | Event |
|---|---|
| T+0h | Error confirmed: Failed to resolve 'api.mimio.ai' |
| T+0.5h | DNS validation: pi.mimio.ai confirmed unreachable |
| T+1h | Correct endpoint identified: pi.xiaomimimo.com |
| T+1.5h | Code fixes applied across all files |
| T+2h | Tests written and verified (31/31 pass) |
| T+2.5h | Backend restarted with corrected configuration |
| T+3h | Health endpoint verified: mimo-v2.5-pro registered correctly |

---

## 3. Root Cause Analysis

### 3.1 The Problem
`
HTTPSConnectionPool(host='api.mimio.ai', port=443):
Failed to resolve 'api.mimio.ai'
([Errno -5] No address associated with hostname)
`

### 3.2 Root Cause
The codebase hardcoded https://api.mimio.ai/v1 as the MiMo API endpoint. This hostname **does not exist** — it fails DNS resolution from HTTP clients.

### 3.3 Correct Endpoint
`
api.xiaomimimo.com ? mimo-pri-alisgp.alb.xiaomi.com ? 8 IPs
`

### 3.4 Secondary Issues
| Issue | Old Value | Correct Value |
|---|---|---|
| Endpoint | pi.mimio.ai | pi.xiaomimimo.com |
| Model Name | mimio-2.5-pro | mimo-v2.5-pro |

---

## 4. Files Fixed

| # | File | Change | Status |
|---|---|---|---|
| 1 | 
oray/config.py | Endpoint + model name + removed hardcoded key | ? Fixed |
| 2 | 
oray/llm/providers/mimio_provider.py | Complete rewrite with validation | ? Fixed |
| 3 | 
oray/config/provider_routing.yaml | Added mimio to preferred_models | ? Fixed |
| 4 | 
oray/llm/health_monitor.py | Added mimio to ALL_PROVIDERS | ? Fixed |
| 5 | 
oray/llm/factory.py | Added mimio/xiaomi mapping | ? Fixed |
| 6 | cademic_demo/components/api.py | Updated endpoint + model | ? Fixed |
| 7 | .env | Added MIMIO_BASE_URL + MIMIO_MODEL | ? Fixed |
| 8 | .env.example | Updated template | ? Fixed |

---

## 5. Connectivity Verification

### 5.1 DNS Resolution
`
api.xiaomimimo.com
  ? CNAME: mimo-pri-alisgp.alb.xiaomi.com
  ? 8 IPs: 8.222.143.90, 47.84.2.69, 47.84.235.191, ...
`

### 5.2 HTTPS Connection
`
GET https://api.xiaomimimo.com/v1/models
Status: 401 (Invalid API Key — endpoint is LIVE)
`

### 5.3 Health Endpoint
`json
{
  "status": "healthy",
  "gateway": {
    "models": ["mimo-v2.5-pro", ...],
    "provider_states": {
      "local": true,
      "anthropic": true,
      "openrouter": true
    }
  }
}
`

---

## 6. Test Results

`
tests/test_mimio_provider.py: 31/31 passed (1.59s)

? Error classification (DNS, connection, SSL, auth, rate limit, timeout, server)
? Provider initialization (default endpoint, custom endpoint, API key)
? Health checks (no key, no URL)
? Endpoint validation (no URL, no key, DNS failure, auth failure, success)
? Generate error handling (no key, no URL, auth error, connection error, success)
? Status API (get_status_dict, diagnostics_to_dict)
`

---

## 7. Fallback Chain

The SmartRouter fallback chain is configured as:

`
mimio ? gemini ? openrouter ? together ? deepseek ? ollama ? openai ? anthropic ? mistral
`

If Mimio is unavailable (no API key, network issue), the system automatically fails over to the next healthy provider.

---

## 8. Remaining Action Items

### User Actions Required
| # | Action | Priority | Where |
|---|---|---|---|
| 1 | Obtain valid API key from https://platform.xiaomimimo.com | Critical | User |
| 2 | Set MIMIO_API_KEY in .env | Critical | User |
| 3 | Set MIMIO_API_KEY in Streamlit secrets (if deploying) | Critical | User |
| 4 | Set MIMIO_API_KEY in Render env vars (if deploying) | Critical | User |

### Configuration Required
`ash
# In .env file
MIMIO_API_KEY=your-key-from-platform.xiaomimimo.com
MIMIO_BASE_URL=https://api.xiaomimimo.com/v1
MIMIO_MODEL=mimo-v2.5-pro
`

---

## 9. Validation Checklist

| Check | Status |
|---|---|
| pi.xiaomimimo.com resolves via DNS | ? PASS |
| HTTPS connection succeeds | ? PASS |
| 401 returned without API key (endpoint is live) | ? PASS |
| mimo-v2.5-pro in model registry | ? PASS |
| mimio in ALL_PROVIDERS | ? PASS |
| Fallback chain configured | ? PASS |
| 31/31 tests pass | ? PASS |
| Health endpoint shows correct model | ? PASS |
| No hardcoded API keys | ? PASS |
| No pi.mimio.ai references remain | ? PASS |

---

## 10. Conclusion

The Mimio provider integration has been completely remediated:

1. **Root cause identified**: Dead endpoint pi.mimio.ai
2. **Correct endpoint verified**: pi.xiaomimimo.com resolves and responds
3. **Code fixed**: All references updated across 8 files
4. **Tests written**: 31 automated tests verify all error paths
5. **Backend restarted**: Configuration loaded correctly
6. **Health verified**: All systems operational

**The system is production-ready pending API key configuration by the user.**

---

*This report was generated as part of the NORAY OS Mimio Provider Incident Resolution.*
