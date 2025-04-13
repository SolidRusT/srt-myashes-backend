#!/bin/bash

# MyAshes.ai Network Development Initialization Script

# Print colorful status messages
print_status() {
  echo -e "\e[1;34m[INFO]\e[0m $1"
}

print_success() {
  echo -e "\e[1;32m[SUCCESS]\e[0m $1"
}

print_error() {
  echo -e "\e[1;31m[ERROR]\e[0m $1"
}

# Check for required commands
check_command() {
  if ! command -v $1 &> /dev/null; then
    print_error "$1 is required but not installed. Please install it and try again."
    exit 1
  fi
}

check_command docker
check_command "docker compose"

# Get hostname
HOST_NAME=$(hostname)
print_status "Detected hostname: $HOST_NAME"

# Create .env file if it doesn't exist
if [ ! -f "docker/.env" ]; then
  print_status "Creating .env file from example..."
  cp docker/.env.example docker/.env
  print_success "Created .env file. Please edit it with your API keys and configuration."
else
  print_status ".env file already exists. Skipping creation."
fi

# Create required directories
print_status "Creating required directories..."
mkdir -p nginx/www
mkdir -p nginx/www/.well-known/acme-challenge
print_success "Created required directories."

# Prompt for API key
read -p "Enter your OpenAI API key: " OPENAI_API_KEY
read -p "Enter comma-separated game server names: " GAME_SERVERS
GAME_SERVERS=${GAME_SERVERS:-"Alpha-1,Alpha-2"}

# Update .env file with provided values
print_status "Updating .env file with your configuration..."
if [ -n "$OPENAI_API_KEY" ]; then
  sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$OPENAI_API_KEY/" docker/.env
fi
sed -i "s/GAME_SERVERS=.*/GAME_SERVERS=$GAME_SERVERS/" docker/.env
print_success "Updated .env file."

# Create a unique Redis password
REDIS_PASSWORD=$(openssl rand -hex 16)
sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" docker/.env
print_success "Generated secure Redis password."

# Ensure proper CORS settings for network development
sed -i "s|BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=[\"http://localhost\", \"http://localhost:3000\", \"http://localhost:8000\", \"http://$HOST_NAME\", \"http://$HOST_NAME:3000\", \"http://$HOST_NAME:8000\", \"*\"]|" docker/.env
print_success "Set CORS settings for network development."

# Update server_name in Nginx config
print_status "Updating Nginx configuration for hostname: $HOST_NAME"
sed -i "s/server_name localhost.*/server_name localhost $HOST_NAME;/" nginx/conf/local.conf
print_success "Updated Nginx configuration."

# Update the Next.js hostname environment
print_status "Configuring Next.js to bind to all interfaces"
sed -i "s/- NEXT_PUBLIC_HOSTNAME=.*/- NEXT_PUBLIC_HOSTNAME=$HOST_NAME/" docker/docker-compose.yml
print_success "Updated Next.js configuration."

# Pull required Docker images
print_status "Pulling required Docker images..."
docker compose -f docker/docker-compose.yml pull
print_success "Pulled Docker images."

# Stop any existing containers and removing them
print_status "Stopping and removing any existing containers..."
docker compose -f docker/docker-compose.yml down
print_success "Stopped and removed containers."

# Start the environment
print_status "Starting Docker containers..."
docker compose -f docker/docker-compose.yml up -d
print_success "Started Docker containers."

# Wait for the services to initialize
print_status "Waiting for services to initialize (30 seconds)..."
sleep 30
print_success "Services should now be initialized."

# Display next steps
echo ""
print_success "Initialization completed successfully!"
echo ""
echo "Next steps:"
echo "1. Access the application at http://$HOST_NAME:3000"
echo "2. Access the API at http://$HOST_NAME:8000/docs"
echo ""
echo "Frontend URL: http://$HOST_NAME:3000"
echo "API URL: http://$HOST_NAME:8000/docs (for API documentation)"
echo ""
echo "To check container status:"
echo "  docker compose -f docker/docker-compose.yml ps"
echo ""
echo "To view logs:"
echo "  docker compose -f docker/docker-compose.yml logs -f"
echo ""
echo "To check specific container logs (e.g., backend):"
echo "  docker compose -f docker/docker-compose.yml logs backend -f"
echo ""