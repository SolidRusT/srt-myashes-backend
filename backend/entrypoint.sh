#!/bin/sh
set -e

# Wait for PostgreSQL to be available
echo "Waiting for PostgreSQL to start..."
while ! nc -z ${POSTGRES_HOST:-localhost} ${POSTGRES_PORT:-5432}; do
  sleep 1
  echo "Still waiting for PostgreSQL..."
done
echo "PostgreSQL started"

# Wait for Redis (optional - only if configured)
if [ -n "$REDIS_HOST" ]; then
  echo "Waiting for Redis to start..."
  timeout=30
  counter=0
  while ! nc -z $REDIS_HOST ${REDIS_PORT:-6379} && [ $counter -lt $timeout ]; do
    sleep 1
    counter=$((counter+1))
    echo "Still waiting for Redis ($counter/$timeout)..."
  done

  if [ $counter -lt $timeout ]; then
    echo "Redis started"
  else
    echo "Warning: Timed out waiting for Redis, but continuing anyway"
  fi
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
if [ "$DEBUG" = "true" ]; then
  echo "Running in debug mode with auto-reload"
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  echo "Running in production mode"
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-4}
fi
