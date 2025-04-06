#!/bin/bash

# Fix script for MyAshes.ai Docker setup
# This script will check and fix common issues with the Docker environment

# Text styling
BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=== MyAshes.ai Docker Fix Tool ===${NC}\n"

# Check if .env file exists
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}No .env file found. Creating from example...${NC}"
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo -e "${GREEN}Created .env file from .env.example${NC}"
    echo -e "${RED}IMPORTANT: Edit .env file to set required API keys and passwords${NC}"
  else
    echo -e "${RED}Error: .env.example file not found!${NC}"
    exit 1
  fi
fi

# Check if docker-compose command is available
if ! command -v docker-compose &> /dev/null; then
  echo -e "${YELLOW}docker-compose command not found. Trying docker compose...${NC}"
  DOCKER_COMPOSE="docker compose"
else
  DOCKER_COMPOSE="docker-compose"
fi

# Stop all containers
echo -e "\n${BOLD}Stopping all containers...${NC}"
$DOCKER_COMPOSE down
echo -e "${GREEN}Done${NC}"

# Prune unused volumes (optional)
echo -e "\n${BOLD}Do you want to prune unused volumes to start clean? (y/n)${NC}"
read -r answer
if [[ $answer =~ ^[Yy]$ ]]; then
  echo -e "${YELLOW}Pruning unused volumes...${NC}"
  docker volume prune -f
  echo -e "${GREEN}Done${NC}"
fi

# Check and fix permissions for entrypoint scripts
echo -e "\n${BOLD}Checking entrypoint script permissions...${NC}"
if [ -f "../backend/entrypoint.sh" ]; then
  chmod +x ../backend/entrypoint.sh
  echo -e "${GREEN}Fixed backend entrypoint.sh permissions${NC}"
fi

if [ -f "../data-pipeline/entrypoint.sh" ]; then
  chmod +x ../data-pipeline/entrypoint.sh
  echo -e "${GREEN}Fixed data-pipeline entrypoint.sh permissions${NC}"
fi

# Rebuild containers
echo -e "\n${BOLD}Rebuilding containers...${NC}"
$DOCKER_COMPOSE build --no-cache
echo -e "${GREEN}Done${NC}"

# Start containers with proper dependencies
echo -e "\n${BOLD}Starting containers in dependency order...${NC}"
echo -e "${YELLOW}1. Starting database containers...${NC}"
$DOCKER_COMPOSE up -d postgres redis etcd minio
echo -e "${GREEN}Database containers started${NC}"

echo -e "${YELLOW}2. Waiting for PostgreSQL to be ready...${NC}"
attempt=0
max_attempts=30
until $DOCKER_COMPOSE exec postgres pg_isready -U postgres || [ $attempt -eq $max_attempts ]; do
  echo "Waiting for PostgreSQL to be ready... ($attempt/$max_attempts)"
  attempt=$((attempt+1))
  sleep 2
done

if [ $attempt -eq $max_attempts ]; then
  echo -e "${RED}PostgreSQL did not become ready in time!${NC}"
else
  echo -e "${GREEN}PostgreSQL is ready${NC}"
fi

echo -e "${YELLOW}3. Starting Milvus...${NC}"
$DOCKER_COMPOSE up -d milvus-standalone
echo -e "${GREEN}Milvus started${NC}"

echo -e "${YELLOW}4. Starting backend...${NC}"
$DOCKER_COMPOSE up -d backend
echo -e "${GREEN}Backend started${NC}"

echo -e "${YELLOW}5. Starting frontend...${NC}"
$DOCKER_COMPOSE up -d frontend
echo -e "${GREEN}Frontend started${NC}"

echo -e "${YELLOW}6. Starting nginx...${NC}"
$DOCKER_COMPOSE up -d nginx
echo -e "${GREEN}Nginx started${NC}"

echo -e "${YELLOW}7. Starting data-pipeline...${NC}"
$DOCKER_COMPOSE up -d data-pipeline
echo -e "${GREEN}Data-pipeline started${NC}"

# Check container status
echo -e "\n${BOLD}${BLUE}Checking container status...${NC}"
$DOCKER_COMPOSE ps

echo -e "\n${BOLD}${BLUE}=== Fix Complete ===${NC}"
echo -e "If containers are still failing, run ./diagnose.sh to see specific error messages."
echo -e "You may need to check the following:"
echo -e "1. Ensure your .env file has all required configuration"
echo -e "2. Check backend logs with: docker-compose logs backend"
echo -e "3. Check Milvus logs with: docker-compose logs milvus-standalone"
echo -e "4. Verify network configurations and port availability"
