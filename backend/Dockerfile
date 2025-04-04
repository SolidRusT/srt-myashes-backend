FROM nvidia/cuda:12.2.0-base-ubuntu22.04

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app

# Expose API port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
