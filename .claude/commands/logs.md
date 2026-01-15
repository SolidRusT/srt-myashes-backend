# /logs - View MyAshes Backend Logs

View recent logs from the myashes-backend pods.

## Instructions

Use the **Kubernetes MCP tools** to fetch logs:

### Basic Logs

Use `mcp__kubernetes__kubectl_logs` with:
- resourceType: "deployment"
- name: "myashes-backend"
- namespace: "myashes-backend"
- tail: 100

### Error-Focused Search

After fetching logs, filter and highlight:
- ERROR, Exception, Traceback
- Failed, Critical
- 5xx HTTP status codes

### Previous Container Logs (if pod restarted)

Use `mcp__kubernetes__kubectl_logs` with:
- resourceType: "deployment"
- name: "myashes-backend"
- namespace: "myashes-backend"
- tail: 100
- previous: true

## Report Summary

After viewing logs, summarize:
- Any errors or exceptions found
- Request patterns (endpoints being hit)
- Response times if visible
- Recommended actions if issues detected
