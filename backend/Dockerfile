# syntax=docker/dockerfile:1
# Stage 1: build the React frontend inside the image so a fresh clone does not
# need a host-side `npm ci && npm run build` step. See ADR 0019.
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci
COPY frontend/ ./frontend/
RUN npm --prefix frontend run build

FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install build dependencies for packages that may not have Python 3.14 wheels yet
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata and lockfile (context is repo-root; see docker-compose.yml)
COPY backend/pyproject.toml backend/uv.lock ./

# Install production dependencies using the lockfile
RUN uv sync --no-dev --frozen

# Copy application code
COPY backend/app ./app

# Copy the built frontend (same-origin serving from app/main.py)
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
