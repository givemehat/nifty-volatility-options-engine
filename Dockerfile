# Multi-service Python container for AlphaGrey Analytics Engine
FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create data directories
RUN mkdir -p data/raw/ohlcv data/raw/options_chain data/processed data/database

# Default port exposure
EXPOSE 8000 8501

# Entrypoint default runs FastAPI
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
