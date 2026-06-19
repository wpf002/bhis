FROM python:3.11-slim

# System deps. build-essential/libpq for builds; the commented libs are the
# WeasyPrint runtime (uncomment if you enable PDF export).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    # libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

# Run as a non-root user.
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Hosts (Railway/Render/Fly) inject $PORT; start.sh migrates then binds to it.
ENV PORT=8000
EXPOSE 8000
CMD ["./start.sh"]
