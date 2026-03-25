# Docker file - to-backend
FROM python:3.11-slim-buster

# Set working directory
WORKDIR /app

# Copy only requirements first for better layer caching
COPY --chown=1001:1001 requirements.txt /app/

# Install Python dependencies in a single layer
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code (this layer changes most frequently)
COPY --chown=1001:1001 ./ /app/

# Set execute permissions on entrypoint script AFTER copying all files
RUN chmod +x /app/cron_jobs/entrypoint.sh

# Create home directory for user 1001 and set proper permissions
RUN mkdir -p /home/appuser && chown -R 1001:1001 /home/appuser && chmod -R u+w /home/appuser

# Ensure /app directory is writable by user 1001 for log files
RUN chown -R 1001:1001 /app && chmod -R u+w /app

# Expose port
EXPOSE 8081

# Switch to non-root user
USER 1001

# Set HOME environment variable
ENV HOME=/home/appuser

# Set entrypoint
ENTRYPOINT ["/app/cron_jobs/entrypoint.sh"]