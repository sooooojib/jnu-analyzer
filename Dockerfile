# ==============================================================================
# Multi-Stage Production Dockerfile for JnU Analyzer
# Lean, secure, and optimized for free-tier hosting (512MB RAM)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build React 19 Frontend
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --prefer-offline --no-audit

COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Python Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    PORT=8000 \
    UPLOAD_DIR=/tmp/result_analyzer/uploads

WORKDIR /app

# Install system dependencies (curl for health check probe)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python production dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy Backend Application
COPY backend/ /app/backend/

# Copy compiled React frontend assets for static collection & SPA serving
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Prepare temporary storage and collect static assets
WORKDIR /app/backend
RUN mkdir -p /tmp/result_analyzer/uploads /app/backend/staticfiles \
    && python manage.py collectstatic --noinput

# Create non-root user for hardened container security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app /tmp/result_analyzer

USER appuser

EXPOSE 8000

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health/ || exit 1

# Production Entrypoint: Run migrations then start Gunicorn
CMD sh -c "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -"
