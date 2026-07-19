# Environment Variables

Create a `.env` file in the root directory. The setup scripts will generate a default one for you.

## Database & Services
```env
ENVIRONMENT=development

POSTGRES_USER=noray
POSTGRES_PASSWORD=noray_dev
POSTGRES_DB=noray_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

QDRANT_HOST=localhost
QDRANT_PORT=6333

REDIS_HOST=localhost
REDIS_PORT=6379
```

## AI Gateway / Cloud Providers
You must configure at least one provider if you are not using Local AI offline.
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIzaSy...
OPENROUTER_API_KEY=sk-or-v1-...
```

## Local AI (Ollama)
```env
OLLAMA_BASE_URL=http://localhost:11434
# Force the router to use local models exclusively
ALLOW_OFFLINE=true
```

## Internal Settings
```env
EMBEDDING_MODEL_KEY=bge-m3
AI_PROVIDER=auto  # Can be forced to 'local', 'openai', 'anthropic', 'gemini', 'openrouter'
```
