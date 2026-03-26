# Docker file - to-backend
FROM python:3.11-slim-buster

# Set working directory
WORKDIR /app

# Install Docker CLI to enable `docker exec` commands
RUN apt-get update && \
    apt-get install -y --no-install-recommends docker.io && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better layer caching
COPY requirements.txt /app/

# Install Python dependencies in a single layer
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code (this layer changes most frequently)
COPY ./ /app/

# Set execute permissions on entrypoint script AFTER copying all files
RUN chmod +x /app/cron/entrypoint.sh

# Expose port
EXPOSE 8081

# Set HOME environment variable
ENV HOME=/root

# Set entrypoint
ENTRYPOINT ["/app/cron/entrypoint.sh"]