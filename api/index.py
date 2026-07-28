"""
NORAY OS — Vercel Serverless Entrypoint

This file wraps the FastAPI app for deployment on Vercel's serverless runtime.
It ensures the app is importable as a WSGI/ASGI handler.

Environment variables needed for Vercel deployment:
  EMBEDDINGS_PROVIDER=openai    (or jina/voyage — avoids local torch dependency)
  VECTOR_STORE_PROVIDER=faiss   (pure NumPy, no qdrant-client needed)
  QDRANT_URL=<remote qdrant>    (if using Qdrant Cloud instead of faiss)
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")

from noray.api.app import app  # noqa: E402

