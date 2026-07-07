# Stage 1: Build
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlite3-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

RUN pip install --no-cache-dir \
    fastapi \
    'uvicorn[standard]' \
    aiosqlite \
    'sqlalchemy[asyncio]' \
    httpx \
    lxml \
    watchfiles \
    python-multipart

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/venv /app/venv

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

ENV PYTHONPATH=/app
ENV PATH="/app/venv/bin:$PATH"

EXPOSE 8099

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8099"]
