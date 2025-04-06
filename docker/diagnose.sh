#!/bin/bash

# Diagnostic script for MyAshes.ai Docker containers
# Shows concise error logs for problematic containers

# Text styling
BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=== MyAshes.ai Container Diagnostic Tool ===${NC}\n"

# Get all container IDs and names
CONTAINERS=$(docker ps -a --format "{{.ID}}|{{.Names}}|{{.Status}}")

# Function to get relevant logs for a container
get_container_logs() {
  CONTAINER_ID=$1
  CONTAINER_NAME=$2
  
  echo -e "${BOLD}${YELLOW}Checking $CONTAINER_NAME${NC}"
  
  # Get the last 50 lines of logs
  LOGS=$(docker logs --tail 50 $CONTAINER_ID 2>&1)
  
  # Extract unique error messages, focusing on common error patterns
  ERROR_LOGS=$(echo "$LOGS" | grep -i 'error\|exception\|fatal\|fail\|denied\|cannot\|unable' | sort | uniq)
  
  if [ -z "$ERROR_LOGS" ]; then
    echo -e "  ${GREEN}No obvious errors found in recent logs${NC}"
    echo -e "  ${YELLOW}Showing last 5 log lines:${NC}"
    docker logs --tail 5 $CONTAINER_ID 2>&1
  else
    echo -e "  ${RED}Found potential errors:${NC}"
    echo "$ERROR_LOGS" | sed 's/^/  /'
  fi
  
  echo ""
}

# Check container status and analyze failing ones
echo -e "${BOLD}Container Status:${NC}"
while IFS='|' read -r ID NAME STATUS; do
  if [[ $STATUS == *"Restarting"* || $STATUS == *"Exited"* ]]; then
    echo -e "❌ $NAME - ${RED}$STATUS${NC}"
    FAILING_CONTAINERS="$FAILING_CONTAINERS $ID|$NAME"
  else
    echo -e "✅ $NAME - ${GREEN}$STATUS${NC}"
  fi
done <<< "$CONTAINERS"

echo -e "\n${BOLD}${BLUE}=== Analyzing Failing Containers ===${NC}\n"

# Analyze each failing container
if [ -z "$FAILING_CONTAINERS" ]; then
  echo -e "${GREEN}No failing containers found!${NC}"
else
  while IFS=' ' read -r CONTAINER; do
    if [ ! -z "$CONTAINER" ]; then
      IFS='|' read -r ID NAME <<< "$CONTAINER"
      get_container_logs "$ID" "$NAME"
    fi
  done <<< "$FAILING_CONTAINERS"
fi

# Check for network connectivity issues
echo -e "${BOLD}${BLUE}=== Checking Network Connectivity ===${NC}\n"

# Check if containers can reach each other
echo -e "${BOLD}Testing inter-container connectivity:${NC}"
RUNNING_CONTAINER=$(docker ps -q | head -n 1)
if [ ! -z "$RUNNING_CONTAINER" ]; then
  echo "Testing from container $RUNNING_CONTAINER:"
  
  # Try to ping Milvus
  echo -n "  Milvus: "
  if docker exec $RUNNING_CONTAINER ping -c 1 milvus-standalone 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
  else
    echo -e "${RED}FAILED${NC}"
  fi
  
  # Try to ping PostgreSQL
  echo -n "  PostgreSQL: "
  if docker exec $RUNNING_CONTAINER ping -c 1 postgres 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
  else
    echo -e "${RED}FAILED${NC}"
  fi
  
  # Try to ping Redis
  echo -n "  Redis: "
  if docker exec $RUNNING_CONTAINER ping -c 1 redis 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
  else
    echo -e "${RED}FAILED${NC}"
  fi
else
  echo -e "${YELLOW}No running containers available for connectivity test${NC}"
fi

echo -e "\n${BOLD}${BLUE}=== Environment Configuration Check ===${NC}\n"

# Check if .env file exists and has required variables
if [ -f ".env" ]; then
  echo -e "${GREEN}.env file exists${NC}"
  
  # Check for important environment variables
  echo -e "\n${BOLD}Checking critical environment variables:${NC}"
  
  # Define required variables
  REQUIRED_VARS=("POSTGRES_USER" "POSTGRES_PASSWORD" "MILVUS_USER" "MILVUS_PASSWORD" "REDIS_PASSWORD" "OPENAI_API_KEY")
  
  for VAR in "${REQUIRED_VARS[@]}"; do
    if grep -q "^$VAR=" .env; then
      VALUE=$(grep "^$VAR=" .env | cut -d '=' -f2)
      if [ -z "$VALUE" ]; then
        echo -e "  $VAR: ${RED}Empty${NC}"
      else
        MASKED="${VALUE:0:3}*****"
        echo -e "  $VAR: ${GREEN}Set ($MASKED)${NC}"
      fi
    else
      echo -e "  $VAR: ${RED}Missing${NC}"
    fi
  done
else
  echo -e "${RED}.env file not found! This is required for container configuration.${NC}"
fi

echo -e "\n${BOLD}${BLUE}=== Recommendations ===${NC}\n"
echo -e "1. Check the logs for the specific error messages shown above"
echo -e "2. Verify that all required environment variables are properly set"
echo -e "3. Make sure the PostgreSQL database is properly initialized"
echo -e "4. Check for port conflicts on your host machine"
echo -e "5. For Milvus issues, verify its configuration and dependencies"
echo -e "6. For nginx issues, check its configuration files"
echo -e "7. Run 'docker-compose down -v' and then 'docker-compose up -d' to rebuild with clean volumes"

echo -e "\n${BOLD}${BLUE}=== End of Diagnostics ===${NC}"
