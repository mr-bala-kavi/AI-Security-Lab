# AI Security Lab - Container image
# Educational platform for AI/ML security vulnerabilities.
#
# Build:  docker build -t ai-security-lab .
# Run:    docker run -p 5000:5000 ai-security-lab
#
# The image installs the full ML stack (CPU-only torch) so every module works.
# Models are downloaded lazily on first use; mount a volume on /app/models/cache
# to persist them between runs.

FROM python:3.11-slim AS base

# Avoid interactive prompts and keep Python output unbuffered for logs.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_ENV=production \
    HOST=0.0.0.0 \
    PORT=5000

WORKDIR /app

# System deps occasionally needed by Pillow / numpy wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching).
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the application.
COPY . .

# Run as a non-root user.
RUN useradd --create-home --uid 1000 labuser \
    && mkdir -p logs models/cache database static/uploads \
    && chown -R labuser:labuser /app
USER labuser

EXPOSE 5000

# Basic container healthcheck against the dashboard.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:5000/ || exit 1

CMD ["python", "app.py"]
