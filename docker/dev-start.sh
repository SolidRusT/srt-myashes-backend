#!/bin/bash

# Development startup script for MyAshes.ai
# This script will set up all the necessary components for local development

# Text styling
BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=== MyAshes.ai Development Startup ===${NC}\n"

# Ensure we're in the docker directory
cd "$(dirname "$0")"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if docker-compose command is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}docker-compose command not found. Using 'docker compose' instead...${NC}"
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Check or create .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}No .env file found. Creating from example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env file from .env.example${NC}"
        
        # Automatically set some defaults for development
        sed -i 's/OPENAI_API_KEY=your_openai_api_key_here/OPENAI_API_KEY=dummy_key_for_dev/' .env
        sed -i 's/DISCORD_BOT_ENABLED=false/DISCORD_BOT_ENABLED=false/' .env
        sed -i 's/DEBUG=false/DEBUG=true/' .env
        sed -i 's/LOG_LEVEL=info/LOG_LEVEL=debug/' .env
        
        echo -e "${YELLOW}Updated .env with development defaults${NC}"
        echo -e "${RED}NOTE: Set a real OPENAI_API_KEY in .env for LLM functionality!${NC}"
    else
        echo -e "${RED}Error: .env.example file not found!${NC}"
        exit 1
    fi
fi

# Create required directories
echo -e "\n${BOLD}Creating required directories...${NC}"
mkdir -p ../nginx/www
mkdir -p ../nginx/ssl
mkdir -p ../nginx/letsencrypt

# Check for files in nginx/www directory
if [ ! -f "../nginx/www/404.html" ]; then
    echo -e "${YELLOW}Creating default 404.html...${NC}"
    cat > ../nginx/www/404.html << EOL
<!DOCTYPE html>
<html>
<head>
    <title>404 - Page Not Found</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { font-size: 36px; margin-bottom: 20px; }
        p { font-size: 18px; }
    </style>
</head>
<body>
    <h1>404 - Page Not Found</h1>
    <p>The page you are looking for does not exist.</p>
    <p><a href="/">Return to home</a></p>
</body>
</html>
EOL
fi

if [ ! -f "../nginx/www/50x.html" ]; then
    echo -e "${YELLOW}Creating default 50x.html...${NC}"
    cat > ../nginx/www/50x.html << EOL
<!DOCTYPE html>
<html>
<head>
    <title>Server Error</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { font-size: 36px; margin-bottom: 20px; }
        p { font-size: 18px; }
    </style>
</head>
<body>
    <h1>Server Error</h1>
    <p>Sorry, something went wrong on our end.</p>
    <p><a href="/">Return to home</a></p>
</body>
</html>
EOL
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

# Stop any running containers
echo -e "\n${BOLD}Stopping any running containers...${NC}"
$DOCKER_COMPOSE down
echo -e "${GREEN}Done${NC}"

# Ask user if they want to rebuild containers
echo -e "\n${BOLD}Do you want to rebuild containers? (y/n)${NC}"
read -r rebuild
if [[ $rebuild =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Rebuilding containers...${NC}"
    $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
    echo -e "${GREEN}Done${NC}"
fi

# Ask user if they want to start fresh (prune volumes)
echo -e "\n${BOLD}Do you want to start fresh by pruning all volumes? (y/n)${NC}"
echo -e "${RED}WARNING: This will delete all data!${NC}"
read -r prune
if [[ $prune =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Pruning volumes...${NC}"
    $DOCKER_COMPOSE down -v
    docker volume prune -f
    echo -e "${GREEN}Done${NC}"
fi

# Start containers in dependency order
echo -e "\n${BOLD}Starting containers in dependency order...${NC}"

echo -e "${YELLOW}1. Starting database and support services...${NC}"
$DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis etcd minio
echo -e "${GREEN}Database services started${NC}"

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}2. Waiting for PostgreSQL to be ready...${NC}"
for i in {1..30}; do
    if $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml exec postgres pg_isready -U postgres &> /dev/null; then
        echo -e "${GREEN}PostgreSQL is ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}\nPostgreSQL did not become ready in time. Please check logs.${NC}"
    fi
done

echo -e "${YELLOW}3. Starting Milvus...${NC}"
$DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml up -d milvus-standalone
echo -e "${GREEN}Milvus started${NC}"

# Wait for Milvus to be ready
echo -e "${YELLOW}4. Waiting for Milvus to be ready...${NC}"
sleep 10
echo -e "${GREEN}Continuing (Milvus should be initializing)${NC}"

echo -e "${YELLOW}5. Starting backend...${NC}"
$DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml up -d backend
echo -e "${GREEN}Backend started${NC}"

echo -e "${YELLOW}6. Starting frontend...${NC}"
$DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml up -d frontend
echo -e "${GREEN}Frontend started${NC}"

echo -e "${YELLOW}7. Starting nginx...${NC}"
$DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml up -d nginx
echo -e "${GREEN}Nginx started${NC}"

echo -e "${YELLOW}8. Starting data-pipeline...${NC}"
$DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml up -d data-pipeline
echo -e "${GREEN}Data-pipeline started${NC}"

# Open the application in browser
echo -e "\n${BOLD}${BLUE}Your development environment is now ready!${NC}"
echo -e "- Frontend URL: ${GREEN}http://localhost:80${NC}"
echo -e "- API URL: ${GREEN}http://localhost:80/api${NC}"
echo -e "- Milvus UI: ${GREEN}http://localhost:9091${NC}"

echo -e "\n${BOLD}${BLUE}Container Status:${NC}"
$DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml ps

echo -e "\n${BOLD}${BLUE}Useful Commands:${NC}"
echo -e "- View logs: ${YELLOW}docker-compose logs -f [service_name]${NC}"
echo -e "- Shell into container: ${YELLOW}docker-compose exec [service_name] bash${NC}"
echo -e "- Stop all containers: ${YELLOW}docker-compose down${NC}"
echo -e "- View logs for a specific service: ${YELLOW}docker-compose logs -f [service_name]${NC}"
echo -e "- Run diagnostics: ${YELLOW}./diagnose.sh${NC}"

echo -e "\n${BOLD}${BLUE}=== Development Environment Ready ===${NC}"
