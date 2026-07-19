# Deployment Guide

NORAY is designed to be easily deployable to cloud environments using Docker.

## Production Docker Compose

For production, you should use an optimized `docker-compose.prod.yml` that builds the Next.js frontend into a static container and serves the FastAPI backend via Gunicorn.

1. **Build Images:**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```
2. **Start Services:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Cloud Providers

### AWS / GCP / Azure
- Deploy the frontend to Vercel or AWS Amplify.
- Deploy the FastAPI backend via AWS App Runner, ECS, or Google Cloud Run.
- Use managed databases (RDS for PostgreSQL, Elasticache for Redis) instead of local containers.
- Use a managed Qdrant Cloud cluster for vector embeddings.

### Local AI in Production
If deploying on a secure private cloud with sensitive data, you can provision a GPU instance (e.g., AWS `g5.xlarge`) and run Ollama alongside the backend to keep all LLM queries offline.
