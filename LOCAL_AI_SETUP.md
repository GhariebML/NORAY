# Local AI Setup

NORAY supports a fully offline, privacy-first Local AI experience. The system automatically detects your hardware capabilities and orchestrates the downloading and running of the most optimal local models.

## Hardware Detection Matrix

NORAY uses `GPUtil` and `psutil` to inspect your OS, CPU, RAM, and GPU.

Based on the available memory and compute, the AI Gateway will recommend and auto-install (via Ollama) one of the following models:

| RAM / Compute | Recommended LLM | Parameters | Use Case |
|--------------|-----------------|------------|----------|
| < 16GB RAM | `qwen2.5:3b` | 3B | Basic offline tasks, code assistance |
| 16GB - 32GB RAM | `qwen2.5:7b` | 7B | High-quality reasoning, RAG synthesis |
| 32GB - 64GB RAM | `qwen2.5:14b` | 14B | Near-GPT-4 logic |
| > 64GB RAM | `deepseek-r1:14b` | 14B+ | Advanced multi-step planning |
| NVIDIA GPU >= 12GB | `qwen2.5:14b` | 14B | Accelerated GPU inference |

## Local Embeddings

NORAY relies on local embedding models by default, powered by `sentence-transformers`. This means your documents never leave your machine during the RAG indexing phase.

The system will prioritize models in the following order:
1. **BAAI/bge-m3** (Default)
2. **jinaai/jina-embeddings-v4-base-en**
3. **nomic-ai/nomic-embed-text-v1.5**
4. **intfloat/multilingual-e5-large**

To override the default embedding model, set `EMBEDDING_MODEL_KEY` in your `.env`:
```env
EMBEDDING_MODEL_KEY=nomic-text
```

## Manual Ollama Management

If you prefer to manage models manually, you can use the Ollama CLI:
```bash
ollama run qwen2.5:7b
ollama pull nomic-embed-text
```

Ensure the Ollama API is running and reachable (default: `http://localhost:11434`).
