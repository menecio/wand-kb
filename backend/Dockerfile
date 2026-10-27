FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install build dependencies for packages that may not have Python 3.14 wheels yet
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata and lockfile
COPY pyproject.toml uv.lock ./

# Install production dependencies using the lockfile
RUN uv sync --no-dev --frozen

# Copy application code
COPY app ./app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
