# Environment Variables Audit & Cloud Mapping Report

---

## 🔑 Production Environment Variable Reference

```env
# Deployment & Runtime
ENVIRONMENT=production
PORT=8001
ALLOWED_ORIGINS=https://noray-frontend.vercel.app,http://localhost:3000

# Persistence & Cache
DATABASE_URL=postgresql://noray:noray_dev@postgres-host:5432/noray_db
REDIS_URL=redis://redis-host:6379/0

# Vector Database
VECTOR_STORE_PROVIDER=qdrant
QDRANT_URL=https://qdrant-cluster.cloud.qdrant.io
QDRANT_API_KEY=YOUR_REDACTED_QDRANT_KEY

# LLM Gateway API Keys
GEMINI_API_KEY=YOUR_REDACTED_GEMINI_KEY
OPENROUTER_API_KEY=YOUR_REDACTED_OPENROUTER_KEY
TOGETHER_API_KEY=YOUR_REDACTED_TOGETHER_KEY
DEEPSEEK_API_KEY=YOUR_REDACTED_DEEPSEEK_KEY
OPENAI_API_KEY=YOUR_REDACTED_OPENAI_KEY
```

**Security Audit Result**: Zero hardcoded credentials committed in git repository.
