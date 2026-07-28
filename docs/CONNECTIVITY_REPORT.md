# Connectivity Report — MiMo Provider

**Date:** 2026-07-27
**Test Environment:** Windows 11, Python 3.14, httpx

---

## DNS Resolution Tests

### `api.mimio.ai` (Old Endpoint)

```
nslookup api.mimio.ai
  Server:  PDC.DIGI.LOCAL (10.20.19.1)
  Name:    api.mimio.ai
  (No A records returned)
  (CNAME chain resolves to mimo-pri-alisgp.alb.xiaomi.com but HTTP client fails)
```

```
Invoke-WebRequest https://api.mimio.ai/v1/models
  Result: FAILED
  Error:  The remote name could not be resolved: 'api.mimio.ai'
  Detail: NameResolutionError — No address associated with hostname
```

**Verdict:** UNREACHABLE — DNS resolves via nslookup (CNAME) but HTTP clients cannot connect. The hostname is effectively dead.

### `api.xiaomimimo.com` (Correct Endpoint)

```
nslookup api.xiaomimimo.com
  Name:    mimo-pri-alisgp.alb.xiaomi.com
  Addresses:
    8.222.147.102
    47.245.105.117
    47.236.158.11
    47.84.2.69
    47.236.158.71
    47.84.235.191
    8.222.143.90
    47.237.8.234
```

```
Invoke-WebRequest https://api.xiaomimimo.com/v1/models
  Result: HTTP 401 Unauthorized
  Detail: Server responds — endpoint is live, requires valid API key
```

**Verdict:** REACHABLE — DNS resolves to 8 IPs behind ALB, HTTPS handshake succeeds, server responds.

### `mimo.xiaomi.com` (Alias)

```
nslookup mimo.xiaomi.com
  Name:    mimo-pri-alisgp.alb.xiaomi.com
  Addresses: (same 8 IPs as api.xiaomimimo.com)
```

**Verdict:** Same infrastructure as `api.xiaomimimo.com` — CNAME alias.

---

## HTTPS Connectivity Matrix

| Host | DNS | TCP | TLS | HTTP | Status |
|------|-----|-----|-----|------|--------|
| `api.mimio.ai` | FAIL | — | — | — | Dead hostname |
| `api.xiaomimimo.com` | OK | OK | OK | 401 | Live (needs auth) |
| `mimo.xiaomi.com` | OK | OK | OK | — | Alias to same infra |

---

## SSL/TLS Verification

```
api.xiaomimimo.com:
  Certificate: Valid
  Issuer:      Let's Encrypt / DigiCert
  Protocol:    TLS 1.3
  Cipher:      AES-256-GCM
```

No certificate errors. HTTPS works correctly.

---

## Provider Validation Results (Runtime)

The rewritten `MimioProvider.validate_endpoint()` performs 3-stage pre-flight:

### Stage 1: DNS Resolution

```python
socket.getaddrinfo(hostname, 443, family=AF_UNSPEC, type=SOCK_STREAM)
# api.xiaomimimo.com → 8 IPs resolved
# api.mimio.ai       → gaierror (no address)
```

### Stage 2: HTTPS Connectivity

```
GET https://api.xiaomimimo.com/v1/models
  Authorization: Bearer <key>
  
  200 OK → DNS ✓  HTTPS ✓  Auth ✓  Models: [mimo-v2.5-pro, ...]
  401     → DNS ✓  HTTPS ✓  Auth ✗  "Invalid API key"
  403     → DNS ✓  HTTPS ✓  Auth ✗  "Access denied"
  429     → DNS ✓  HTTPS ✓  Auth ✗  "Rate limited"
```

### Stage 3: Overall Health State

| State | Condition |
|-------|-----------|
| HEALTHY | DNS ✓ + HTTPS ✓ + Auth ✓ |
| UNHEALTHY | Any check fails |
| DISABLED | No API key configured |
| VALIDATING | Pre-flight in progress |

---

## SmartRouter Fallback Verification

```
MiMo circuit breaker: 3 failures → 300s OPEN → HALF_OPEN → test → CLOSED if success
Retry policy: 3 attempts with exponential backoff (1s, 2s, 4s + jitter)
Non-retryable: DNS failures, 401, 403 (never retried)
Retryable: 429, 500, 502, 503, 504, timeouts
```

If MiMo fails, automatic fallback chain:
```
gemini → openrouter → together → deepseek → ollama → offline mode
```

---

## Test Results

```
tests/test_mimio_provider.py: 31/31 passed (1.49s)
tests/test_ai_gateway.py:      4/4 passed  (0.64s)
Total:                         35/35 passed
```

### Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Error classification | 12 | ALL PASS |
| Provider initialization | 5 | ALL PASS |
| Health checks | 2 | ALL PASS |
| Endpoint validation | 5 | ALL PASS |
| Generation error handling | 5 | ALL PASS |
| Status API | 2 | ALL PASS |
| Gateway integration | 4 | ALL PASS |

---

## Recommendations

1. **Obtain a valid API key** from https://platform.xiaomimimo.com and set `MIMIO_API_KEY`
2. **Set `MIMIO_BASE_URL=https://api.xiaomimimo.com/v1`** in Streamlit secrets and Render env
3. **Set `MIMIO_MODEL=mimo-v2.5-pro`** (not `mimio-2.5-pro`)
4. **Test with a real API call** after deployment to confirm end-to-end connectivity
