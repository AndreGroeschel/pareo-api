# Builder stage
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app
ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

# Install dependencies first (for better caching)
COPY pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r pyproject.toml

# Copy the project and install it
COPY ./src /app/src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -e .

# Runtime stage
FROM python:3.13-slim

WORKDIR /app
ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY ./src /app/src

EXPOSE $PORT

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
