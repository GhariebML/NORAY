# AI Models

## Local Models (via Ollama) — ✅ Implemented

| Model | Purpose |
|---|---|
| Llama 3.1 8B | Primary local generation model |
| Qwen 2.5 7B | Alternative local generation model |
| Nomic Embed Text | Default local embedding model |

The Local Runtime Manager detects Ollama automatically and downloads required models on demand. Local models are the default choice for cost-free, privacy-preserving inference.

## Cloud Providers

| Provider | Status | Notes |
|---|---|---|
| Google Gemini | ✅ Integrated | |
| OpenRouter | ✅ Integrated | Gateway to multiple hosted models, including Gemini variants |
| Together AI | ✅ Integrated | |
| DeepSeek | ✅ Integrated | |
| OpenAI | 🔵 Supported by architecture | Requires API key to activate |
| Anthropic | 🔵 Supported by architecture | Requires API key to activate |
| Mistral | 🔵 Supported by architecture | Requires API key to activate |

All providers implement a shared provider interface within the unified LLM Gateway, so adding a new provider does not require changes to the routing or orchestration logic.

## Routing Logic — ✅ Implemented

The Unified LLM Router selects a model per request based on:

- **Provider health** — is the provider currently reachable and within rate limits?
- **Cost** — cost-aware routing prefers cheaper providers for simpler tasks.
- **Latency** — latency-aware routing avoids slow providers under time pressure.
- **Context window needs** — task complexity influences whether a larger-context model is selected.
- **Local-first preference** — local models are tried first when suitable, reducing cost and preserving privacy.

Indicative routing strategy:

```
Simple Tasks
   ↓
Fast / Cheap Cloud Models
   ↓
Local Models
   ↓
High-end Models for Complex Reasoning
```

## Failover — ✅ Implemented

If a selected provider is unavailable (missing API key, rate-limited, or erroring), the router automatically skips it and continues down the fallback chain rather than failing the request outright.

## Cost Optimization — ✅ Implemented

Token usage and estimated cost are tracked per request and surfaced in the AI Telemetry dashboard, informing which provider a given task is routed to.

## Context Windows

Effective context window depends entirely on the selected model/provider and is not fixed system-wide. The router accounts for this when selecting a model for a given task rather than assuming a single global context size.

## Performance Notes

Latency and resource-usage figures shown in the product UI (e.g., "Latency: 320ms", "VRAM 3.4GB") are **illustrative development telemetry**, demonstrating that the observability system works — they are not yet the result of formal, reproducible benchmarking. Formal benchmarking is a planned activity; see [`TESTING.md`](./TESTING.md) and [`DEVELOPMENT_ROADMAP.md`](./DEVELOPMENT_ROADMAP.md).

Observed during development (not a formal benchmark):
- Retrieval typically completes in under 1 second.
- Generation time is provider-dependent — local Ollama models are naturally slower than cloud providers, which are generally faster for comparable tasks.
