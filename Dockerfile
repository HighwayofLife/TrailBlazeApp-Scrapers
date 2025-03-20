FROM python:3.11-slim

WORKDIR /app

# Install curl and other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt .
COPY test_requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r test_requirements.txt

# Copy application code
COPY . .

# Create cache directory
RUN mkdir -p cache && chmod 777 cache

# Run as non-root user for better security
RUN useradd -m appuser
USER appuser

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Default command to run when container starts
CMD ["python", "-m", "app.main"]
