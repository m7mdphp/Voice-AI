FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (needed for gRPC and Firestore)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .
# Copy frontend files so they are available at /app/frontend/
COPY frontend/ ./frontend/

# Expose port
EXPOSE 8000

# Run the application: Correcting Handshake parameters for Proxy resilience
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
