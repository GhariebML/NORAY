# Provider Configuration — Xiaomi MiMo

**Last Updated:** 2026-07-27
**Status:** Production-Ready

---

## Environment Variables

All provider configuration is driven by environment variables. No source code changes are needed to update endpoints, keys, or models.

### Required

| Variable | Value | Description |
|----------|-------|-------------|
| `MIMIO_API_KEY` | *(your key)* | API key from platform.xiaomimimo.com |
| `MIMIO_BASE_URL` | `https://api.xiaomimimo.com/v1` | Official MiMo API endpoint |
| `MIMIO_MODEL` | `mimo-v2.5-pro` | Default model identifier |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PROVIDER` | `auto` | Provider selection (`mimio`, `gemini`, `auto`) |
| `LLM_PROVIDER` | `mimio` | LLM provider override |

---

## Configuration Files

### `.env` (local development)

```env
MIMIO_BASE_URL=https://api.xiaomimimo.com/v1
MIMIO_MODEL=mimo-v2.5-pro
# MIMIO_API_KEY=your-key-here  (set via environment, never committed)
```

### `.env.example` (deployment template)

```env
# Primary Provider: Xiaomi MiMo AI
# Official endpoint: https://platform.xiaomimimo.com
MIMIO_API_KEY=
MIMIO_BASE_URL=https://api.xiaomimimo.com/v1
MIMIO_MODEL=mimo-v2.5-pro
LLM_PROVIDER=mimio
AI_PROVIDER=mimio
```

### `noray/config.py`

```python
MIMIO_API_KEY: str | None = Field(default=None)
MIMIO_BASE_URL: str = Field(default="https://api.xiaomimimo.com/v1")
MIMIO_MODEL: str = Field(default="mimo-v2.5-pro")
AI_PROVIDER: str = Field(default="mimio")
```

### `noray/config/provider_routing.yaml`

```yaml
provider_priority:
  free:
    - mimio        # Priority 1
    - gemini
    - openrouter
    - together
    - groq
    - deepseek
    - huggingface

provider_weights:
  mimio: 50        # Highest load-balancing weight

preferred_models:
  mimio: "mimo-v2.5-pro"
```

---

## Provider Registry

| Field | Value |
|-------|-------|
| Provider Name | `mimio` |
| Aliases | `xiaomi` |
| Factory Registration | `LLMProviderFactory.get_provider("mimio")` |
| Model | `mimo-v2.5-pro` |
| Context Window | 1,000,000 tokens |
| Supports Tools | Yes |
| Supports JSON | Yes |
| Supports Reasoning | Yes |
| Input Cost | $1.00 / 1M tokens |
| Output Cost | $3.00 / 1M tokens |
| Priority | 1 (highest) |
| Circuit Breaker | 3 failures → 300s cooldown |

---

## Fallback Chain

```
MiMo (Priority 1)
  ↓ (if unhealthy / circuit open)
Gemini (Priority 2)
  ↓
OpenRouter (Priority 3)
  ↓
Together (Priority 4)
  ↓
Groq (Priority 5)
  ↓
DeepSeek (Priority 6)
  ↓
HuggingFace (Priority 7)
  ↓
Local Ollama (all models)
  ↓
Emergency Offline Mode
```

---

## Production Endpoints

### Xiaomi MiMo Official

| Component | Value |
|-----------|-------|
| API Base | `https://api.xiaomimimo.com/v1` |
| Chat Completions | `POST /v1/chat/completions` |
| Model List | `GET /v1/models` |
| Embeddings | `POST /v1/embeddings` |
| Auth Header | `Authorization: Bearer <api_key>` |
| API Key Format | `miMo-sk-...` (pay-as-you-go) or `tp-...` (Token Plan) |
| Platform | https://platform.xiaomimimo.com |

### Available Models

| Model ID | Context | Input (per 1M) | Output (per 1M) |
|----------|---------|----------------|-----------------|
| `mimo-v2.5-pro` | 1M | $1.00 | $3.00 |
| `mimo-v2-flash` | 56k | $0.50 | $1.50 |
| `mimo-v2.5-omni` | 128k | $1.50 | $4.00 |
| `mimo-7b-instruct` | 32k | $0.15 | $0.45 |

---

## Secrets Management

### Streamlit Community Cloud

Set in **Streamlit App Settings → Secrets**:

```toml
MIMIO_API_KEY = "your-api-key-here"
MIMIO_BASE_URL = "https://api.xiaomimimo.com/v1"
MIMIO_MODEL = "mimo-v2.5-pro"
```

### Render Backend

Set in **Render Dashboard → Environment**:

```
MIMIO_API_KEY=your-api-key-here
MIMIO_BASE_URL=https://api.xiaomimimo.com/v1
MIMIO_MODEL=mimo-v2.5-pro
```

### Security Rules

- API keys are NEVER committed to source control
- `.env` is in `.gitignore`
- `.env.example` contains empty placeholders only
- Source code defaults to `None` for API keys
- Provider adapter validates key presence before making requests
