#!/bin/bash

# Script to view logs from a specific container or all containers

# Text styling
BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if docker-compose command is available
if ! command -v docker-compose &> /dev/null; then
  echo -e "${YELLOW}docker-compose command not found. Using 'docker compose' instead...${NC}"
  DOCKER_COMPOSE="docker compose"
else
  DOCKER_COMPOSE="docker-compose"
fi

# List available services
services=$($DOCKER_COMPOSE config --services)

# Function to view logs for a specific service
view_logs() {
  service=$1
  lines=$2
  
  echo -e "${BOLD}${BLUE}Viewing logs for $service${NC}\n"
  $DOCKER_COMPOSE logs --tail=$lines -f $service
}

# Display usage information
display_usage() {
  echo -e "${BOLD}${BLUE}=== MyAshes.ai Logs Viewer ===${NC}\n"
  echo -e "Usage: $0 [service] [lines]"
  echo -e "  service: Container service name to view logs for"
  echo -e "  lines: Number of lines to show (default: 50)"
  echo -e "\nAvailable services:"
  
  for service in $services; do
    status=$($DOCKER_COMPOSE ps $service --format json | grep -o '"State":"[^"]*"' | cut -d'"' -f4)
    if [ "$status" = "running" ]; then
      echo -e "  - ${GREEN}$service${NC} (running)"
    else
      echo -e "  - ${RED}$service${NC} ($status)"
    fi
  done
  
  echo -e "\nExamples:"
  echo -e "  $0 backend         # View backend logs"
  echo -e "  $0 backend 100     # View last 100 lines of backend logs"
  echo -e "  $0 all             # View logs from all services"
}

# Main script logic
if [ $# -eq 0 ]; then
  display_usage
  exit 0
fi

service=$1
lines=${2:-50}  # Default to 50 lines if not specified

if [ "$service" = "all" ]; then
  echo -e "${BOLD}${BLUE}Viewing logs for all services${NC}\n"
  $DOCKER_COMPOSE logs --tail=$lines -f
else
  # Check if the service exists
  if echo "$services" | grep -q "^$service$"; then
    view_logs $service $lines
  else
    echo -e "${RED}Error: Service '$service' not found${NC}"
    display_usage
    exit 1
  fi
fi
