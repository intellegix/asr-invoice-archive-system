# ASR Production Server Dockerfile
# Enterprise document processing server with Claude AI integration
# Multi-stage build for optimized production image
#
# Build from asr-systems directory:
#   docker build -f production-server/Dockerfile -t asr-backend .

# Build stage
FROM python:3.11.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY production-server/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11.11-slim AS production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN groupadd -r asruser && useradd -r -g asruser asruser

# Copy application code (from asr-systems context)
COPY production-server/ /app/production-server/
COPY shared/ /app/shared/

# Set Python path to include shared modules
ENV PYTHONPATH=/app:/app/production-server:/app/shared
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create data directories
RUN mkdir -p /app/data/uploads/temp \
    /app/data/processed/open_payable \
    /app/data/processed/closed_payable \
    /app/data/processed/open_receivable \
    /app/data/processed/closed_receivable \
    /app/data/manual_review \
    /app/data/backups \
    /app/logs && \
    chown -R asruser:asruser /app

# Switch to non-root user
USER asruser

# Expose API port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default environment variables
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV DEBUG=false
ENV LOG_LEVEL=INFO
ENV STORAGE_BACKEND=local
ENV DATA_DIR=/app/data

# Start the production server
# PYTHONPATH includes /app/production-server so api.main resolves correctly
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
