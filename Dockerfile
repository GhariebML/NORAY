FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir --user .

FROM python:3.10-slim AS runner

WORKDIR /app

# Install runtime dependencies for parsing & OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tesseract-ocr \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

EXPOSE 8001

ENV PORT=8001
ENV HOST=0.0.0.0

CMD ["python", "-m", "uvicorn", "noray.api.app:app", "--host", "0.0.0.0", "--port", "8001"]
