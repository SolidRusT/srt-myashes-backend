#!/bin/sh

# Wait for PostgreSQL to be available
echo "Waiting for PostgreSQL to start..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 1
  echo "Still waiting for PostgreSQL..."
done
echo "PostgreSQL started"

# Wait for Milvus (optional - only if using it)
if [ "$MILVUS_HOST" != "" ]; then
  echo "Waiting for Milvus to start..."
  # Simple connection test - just try to connect to the port
  timeout=60
  counter=0
  while ! nc -z $MILVUS_HOST $MILVUS_PORT && [ $counter -lt $timeout ]; do
    sleep 1
    counter=$((counter+1))
    echo "Still waiting for Milvus ($counter/$timeout)..."
  done
  
  if [ $counter -lt $timeout ]; then
    echo "Milvus started"
  else
    echo "Warning: Timed out waiting for Milvus, but continuing anyway"
  fi
fi

# Wait for Redis (optional - only if using it)
if [ "$REDIS_HOST" != "" ]; then
  echo "Waiting for Redis to start..."
  timeout=30
  counter=0
  while ! nc -z $REDIS_HOST $REDIS_PORT && [ $counter -lt $timeout ]; do
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
cd /app
alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
if [ "$DEBUG" = "true" ]; then
  echo "Running in debug mode with auto-reload"
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  echo "Running in production mode"
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
