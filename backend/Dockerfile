FROM python:3.12-slim as builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_PREFERENCE=only-system

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install dependencies separately to leverage Docker cache
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project --no-dev --python /usr/local/bin/python

# Install the project
COPY . .
RUN uv sync --no-dev --python /usr/local/bin/python

FROM python:3.12-slim

WORKDIR /app

# Copy the environment from the builder
COPY --from=builder /app /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=.

# Create a non-privileged user to run the app
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --gid 1001 app
USER app

EXPOSE 8000

# Default command runs the API
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
