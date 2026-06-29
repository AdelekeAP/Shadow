# Build stage
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install all deps (torch is CPU-only via --extra-index-url in requirements.txt)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Production stage
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

RUN mkdir -p /app/audio_cache /app/library && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# --forwarded-allow-ips '*' makes the worker trust Railway's proxy headers
# (X-Forwarded-Proto) so FastAPI 307 trailing-slash redirects preserve https
# instead of emitting http:// (which browsers block as mixed content).
CMD ["gunicorn", "app.main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120", "--forwarded-allow-ips", "*"]
