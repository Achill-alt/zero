# ── Backend: Python 3.12 + FastAPI ──────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install system deps (none currently needed beyond slim base)
# gcc/libs are NOT required — all deps are pure Python or precompiled wheels

# Install Python dependencies (layer cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create volume mount points
RUN mkdir -p /app/data/uploads

EXPOSE 8000

# healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Entrypoint: seed DB (idempotent) then start uvicorn
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
