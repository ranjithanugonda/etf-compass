# Multi-stage build for ETF Compass
# Stage 1: Build React frontend
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install --silent
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.13-slim
WORKDIR /app

# System deps for asyncpg, healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps via pyproject.toml
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e . 2>/dev/null; \
    pip install --no-cache-dir \
    fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg \
    alembic pandas yfinance pyarrow python-dateutil \
    redis pyjwt python-dotenv pydantic pydantic-settings

# Copy backend code
COPY backend/ ./backend/
COPY wiki/ ./wiki/
COPY data/ ./data/
COPY WIKI_SCHEMA.md ./

# Copy frontend build
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8080/api/health || exit 1

EXPOSE 8080
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
