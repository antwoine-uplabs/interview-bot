# Use Python 3.12 slim image for smaller footprint
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create final stage with only necessary dependencies
FROM python:3.12-slim

WORKDIR /app

# Copy installed Python packages
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/
COPY .env.example ./.env
COPY interview-content/ ./interview-content/

# Create uploads directory with proper permissions
RUN mkdir -p /app/uploads && chmod 777 /app/uploads

# Set Sentry and LangSmith environment variables
ENV SENTRY_ENVIRONMENT=production
ENV SENTRY_TRACES_SAMPLE_RATE=0.1
ENV LANGSMITH_TRACING_V2=true
ENV LANGCHAIN_TRACING_V2=true
ENV LANGSMITH_PROJECT=interview-evaluator-prod

# Set application environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose the port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--workers", "4"]