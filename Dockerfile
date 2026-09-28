# ==============================================================================
# CloudSky Airways — Production Dockerfile
# ==============================================================================
FROM python:3.11-slim

# Avoid writing .pyc files & force unbuffered stdout/stderr logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000 \
    DATABASE_PATH=/app/data/cloudsky.db

# Set container working directory
WORKDIR /app

# Install system dependencies (curl for healthcheck, sqlite3 for management)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create persistent database folder and dedicated non-root application user
RUN mkdir -p /app/data && \
    useradd -m -u 1001 -s /bin/bash cloudsky && \
    chown -R cloudsky:cloudsky /app

# Switch to non-root user for security
USER cloudsky

# Expose internal container port
EXPOSE 5000

# Container health monitoring probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Launch production WSGI application with Gunicorn
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120 wsgi:app"]
