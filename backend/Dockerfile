FROM nvidia/cuda:12.2.0-base-ubuntu22.04

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app
COPY ./migrations /app/migrations
COPY ./alembic.ini /app/alembic.ini

# Copy and set permissions for entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose API port
EXPOSE 8000

# Use the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
