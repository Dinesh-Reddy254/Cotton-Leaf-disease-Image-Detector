# ── CottonGreen AI — Dockerfile ─────────────────────────────────
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    TF_ENABLE_ONEDNN_OPTS=0 \
    FLASK_ENV=production

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libgomp1 && rm -rf /var/lib/apt/lists/*

# Python deps first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App source
COPY . .

# Create model directory
RUN mkdir -p /app/model

EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/health || exit 1

CMD ["gunicorn", "app:app", \
     "-c", "gunicorn.conf.py", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
