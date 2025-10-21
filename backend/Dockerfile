# Stage 1: Build dependencies with uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim as builder

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Stage 2: Runtime
FROM python:3.12-slim-bookworm

# Install uv for runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Ensure we use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Run with uv
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]