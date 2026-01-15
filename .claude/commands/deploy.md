# /deploy - Build and Deploy MyAshes Backend

Build a new Docker image and deploy to Kubernetes.

## Pre-flight Checks

1. **Check git status** - Verify working directory state:
   ```bash
   git status --short
   ```

2. **Confirm branch** - Ensure on main branch or confirm with user.

## Build Steps

1. **Build Docker image**:
   ```bash
   docker build -t poseidon.hq.solidrust.net:30008/shaun/myashes-backend:latest -f backend/Dockerfile backend/
   ```

2. **Push to Gitea registry**:
   ```bash
   docker push poseidon.hq.solidrust.net:30008/shaun/myashes-backend:latest
   ```

## Deploy Steps (Use Kubernetes MCP)

3. **Rollout restart**: Use `mcp__kubernetes__kubectl_rollout` with:
   - subCommand: "restart"
   - resourceType: "deployment"
   - name: "myashes-backend"
   - namespace: "myashes-backend"

4. **Wait for rollout**: Use `mcp__kubernetes__kubectl_rollout` with:
   - subCommand: "status"
   - resourceType: "deployment"
   - name: "myashes-backend"
   - namespace: "myashes-backend"
   - timeout: "120s"

5. **Verify pods**: Use `mcp__kubernetes__kubectl_get` with:
   - resourceType: "pods"
   - namespace: "myashes-backend"
   - labelSelector: "app=myashes-backend"

6. **Health check**:
   ```bash
   curl -s https://artemis.hq.solidrust.net/api/v1/builds?limit=1 | head -c 100
   ```

## On Failure

Use `mcp__kubernetes__kubectl_logs` with:
- resourceType: "pod"
- namespace: "myashes-backend"
- labelSelector: "app=myashes-backend"
- tail: 50

Check events with `mcp__kubernetes__kubectl_get` for events in myashes-backend namespace.
