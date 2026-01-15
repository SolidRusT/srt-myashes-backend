# /status - Check MyAshes Backend Health

Check the deployment status and health of the myashes-backend service.

## Instructions

Use the **Kubernetes MCP tools** (not bash) to check:

1. **Pod status**: Use `mcp__kubernetes__kubectl_get` with:
   - resourceType: "pods"
   - namespace: "myashes-backend"
   - labelSelector: "app=myashes-backend"

2. **Deployment rollout status**: Use `mcp__kubernetes__kubectl_rollout` with:
   - subCommand: "status"
   - resourceType: "deployment"
   - name: "myashes-backend"
   - namespace: "myashes-backend"

3. **Recent events**: Use `mcp__kubernetes__kubectl_get` with:
   - resourceType: "events"
   - namespace: "myashes-backend"
   - sortBy: "lastTimestamp"

4. **Endpoint health check** (use Bash for external curl):
   ```bash
   curl -s -w "\nHTTP Status: %{http_code}\n" https://artemis.hq.solidrust.net/api/v1/builds?limit=1 | head -c 300
   ```

## Report Format

Summarize findings:
- Pod count and status (Running/Pending/Failed)
- Deployment readiness
- Any warning/error events
- API endpoint responsiveness
- Recommended actions if issues found
