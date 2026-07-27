# Deployment

## Current Deployment Model — ✅ Implemented

NORAY OS is currently deployed and validated as a **local development stack** using Docker Compose:

```yaml
# Representative docker-compose.yml structure
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [qdrant, postgres, redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]

  qdrant:
    image: qdrant/qdrant
    ports: ["6333:6333"]
    volumes: ["qdrant_data:/qdrant/storage"]

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: noray
    volumes: ["postgres_data:/var/lib/postgresql/data"]

  redis:
    image: redis:7
```

This structure is representative of the intended service topology; refer to the repository's actual `docker-compose.yml` for the current, authoritative configuration.

## Live Deployment Status

There is currently **no public live deployment**. NORAY OS runs in local development mode only. A live deployment URL is a placeholder in the submission materials (`[LIVE_DEPLOYMENT_URL]`) pending future hosting decisions.

## Production Readiness Checklist

| Area | Status |
|---|---|
| Containerized services (backend, frontend, Qdrant, Postgres, Redis) | ✅ Implemented |
| Environment-based configuration | ✅ Implemented |
| Authentication / access control | ⚪ Planned |
| Horizontal scaling / load balancing | ⚪ Planned |
| Kubernetes manifests | ⚪ Planned |
| Distributed agent execution | ⚪ Planned |
| Managed cloud hosting | ⚪ Planned |
| CI/CD pipeline | ⚪ Planned |

## Future Roadmap

- **Kubernetes** — containerized services migrating to a Kubernetes deployment for horizontal scaling.
- **Multi-node Execution** — distributing agent/task execution across multiple nodes.
- **Managed Vector Store Option** — evaluating managed Qdrant Cloud vs. self-hosted for production scale.
- **Observability Integration** — exporting telemetry to external monitoring (e.g., Prometheus/Grafana) rather than the in-app dashboard alone.

These items are documented as intent, not current capability.
