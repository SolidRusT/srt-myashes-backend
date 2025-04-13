#!/bin/bash

# MyAshes.ai Project Initialization Script

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
mkdir -p nginx/ssl
mkdir -p nginx/www
mkdir -p nginx/www/.well-known/acme-challenge
mkdir -p nginx/letsencrypt
print_success "Created required directories."

# Prompt for environment configuration
read -p "Enter your domain name (e.g., myashes.ai, leave blank for local development): " DOMAIN_NAME
read -p "Enter your OpenAI API key: " OPENAI_API_KEY
read -p "Enable Discord bot? (y/n): " ENABLE_DISCORD
if [ "$ENABLE_DISCORD" = "y" ] || [ "$ENABLE_DISCORD" = "Y" ]; then
  read -p "Enter your Discord bot token: " DISCORD_BOT_TOKEN
  DISCORD_BOT_ENABLED="true"
else
  DISCORD_BOT_ENABLED="false"
  DISCORD_BOT_TOKEN=""
fi
read -p "Enter comma-separated game server names: " GAME_SERVERS
GAME_SERVERS=${GAME_SERVERS:-"Alpha-1,Alpha-2"}

# Update .env file with provided values
print_status "Updating .env file with your configuration..."
if [ -n "$OPENAI_API_KEY" ]; then
  sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$OPENAI_API_KEY/" docker/.env
fi
sed -i "s/DISCORD_BOT_ENABLED=.*/DISCORD_BOT_ENABLED=$DISCORD_BOT_ENABLED/" docker/.env
if [ -n "$DISCORD_BOT_TOKEN" ]; then
  sed -i "s/DISCORD_BOT_TOKEN=.*/DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN/" docker/.env
fi
sed -i "s/GAME_SERVERS=.*/GAME_SERVERS=$GAME_SERVERS/" docker/.env
print_success "Updated .env file."

# Update Nginx configuration if domain is provided
if [ -n "$DOMAIN_NAME" ]; then
  print_status "Updating Nginx configuration for domain: $DOMAIN_NAME"
  sed -i "s/myashes.ai/$DOMAIN_NAME/g" nginx/conf/myashes.conf
  print_success "Updated Nginx configuration."
fi

# Create a unique Redis password
REDIS_PASSWORD=$(openssl rand -hex 16)
sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" docker/.env
print_success "Generated secure Redis password."

# Pull required Docker images
print_status "Pulling required Docker images..."
docker compose -f docker/docker-compose.yml pull
print_success "Pulled Docker images."

# Start the environment
print_status "Starting Docker containers..."
docker compose -f docker/docker-compose.yml up -d
print_success "Started Docker containers."

# Display next steps
echo ""
print_success "Initialization completed successfully!"
echo ""
if [ -n "$DOMAIN_NAME" ]; then
  echo "Next steps:"
  echo "1. Ensure your domain DNS is configured to point to this server."
  echo "2. Let's Encrypt SSL certificate should be obtained automatically."
  echo "3. Access your application at https://$DOMAIN_NAME"
else
  echo "Next steps:"
  echo "1. Access the application at http://localhost:3000"
  echo "2. Access the API at http://localhost:8000"
fi
echo ""
echo "Frontend URL: http://localhost:3000 (or https://$DOMAIN_NAME)"
echo "API URL: http://localhost:8000/docs (for API documentation)"
echo ""
echo "To check container status:"
echo "  docker compose -f docker/docker-compose.yml ps"
echo ""
echo "To view logs:"
echo "  docker compose -f docker/docker-compose.yml logs -f"
echo ""
