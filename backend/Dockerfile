# ARAP backend production image.
# NOTE: a single uvicorn worker is used because camera workers run in-process
# (one thread per camera). Do NOT run multiple workers or camera pipelines will
# be duplicated.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# OpenCV/ultralytics runtime needs a system GL library on slim images.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user; grant write access for the model/data dirs so the
# YOLO weights can be downloaded on first use and SQLite can be used in dev.
RUN useradd --create-home appuser \
    && mkdir -p /app/models /app/data \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Start with migrations applied, then serve. Production uses a single worker.
CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
