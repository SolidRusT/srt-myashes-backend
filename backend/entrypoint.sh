#!/bin/sh
set -e

# =============================================================================
# Startup retry configuration
# =============================================================================
MAX_RETRIES=${MAX_STARTUP_RETRIES:-30}
BASE_DELAY=2
MAX_DELAY=10

# =============================================================================
# Wait for PostgreSQL with exponential backoff
# =============================================================================
echo "Waiting for PostgreSQL to start..."
retry_count=0
retry_delay=$BASE_DELAY

while [ $retry_count -lt $MAX_RETRIES ]; do
  if nc -z ${POSTGRES_HOST:-localhost} ${POSTGRES_PORT:-5432} 2>/dev/null; then
    echo "PostgreSQL is ready"
    break
  fi
  
  retry_count=$((retry_count + 1))
  echo "PostgreSQL not ready, retrying ($retry_count/$MAX_RETRIES) in ${retry_delay}s..."
  sleep $retry_delay
  
  # Exponential backoff (max MAX_DELAY seconds)
  if [ $retry_delay -lt $MAX_DELAY ]; then
    retry_delay=$((retry_delay * 2))
    if [ $retry_delay -gt $MAX_DELAY ]; then
      retry_delay=$MAX_DELAY
    fi
  fi
done

if [ $retry_count -eq $MAX_RETRIES ]; then
  echo "ERROR: PostgreSQL did not become ready after $MAX_RETRIES attempts"
  exit 1
fi

# =============================================================================
# Wait for Redis (optional - only if configured)
# =============================================================================
if [ -n "$REDIS_HOST" ]; then
  echo "Waiting for Redis to start..."
  retry_count=0
  retry_delay=$BASE_DELAY
  
  while [ $retry_count -lt $MAX_RETRIES ]; do
    if nc -z $REDIS_HOST ${REDIS_PORT:-6379} 2>/dev/null; then
      echo "Redis is ready"
      break
    fi
    
    retry_count=$((retry_count + 1))
    echo "Redis not ready, retrying ($retry_count/$MAX_RETRIES) in ${retry_delay}s..."
    sleep $retry_delay
    
    # Exponential backoff
    if [ $retry_delay -lt $MAX_DELAY ]; then
      retry_delay=$((retry_delay * 2))
      if [ $retry_delay -gt $MAX_DELAY ]; then
        retry_delay=$MAX_DELAY
      fi
    fi
  done

  if [ $retry_count -eq $MAX_RETRIES ]; then
    echo "Warning: Redis did not become ready after $MAX_RETRIES attempts, continuing anyway"
  fi
fi

# =============================================================================
# Run migrations
# =============================================================================
echo "Running database migrations..."
alembic upgrade head

# =============================================================================
# Start the application
# =============================================================================
echo "Starting FastAPI application..."
if [ "$DEBUG" = "true" ]; then
  echo "Running in debug mode with auto-reload"
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  echo "Running in production mode"
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-4}
fi
