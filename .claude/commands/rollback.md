# /rollback - Rollback MyAshes Backend Deployment

Roll back the myashes-backend deployment to a previous revision.

## Instructions

### 1. Check Rollout History

Use `mcp__kubernetes__kubectl_rollout` with:
- subCommand: "history"
- resourceType: "deployment"
- name: "myashes-backend"
- namespace: "myashes-backend"

### 2. Confirm with User

Show the available revisions and ask which revision to roll back to (default: previous).

### 3. Execute Rollback

Use `mcp__kubernetes__kubectl_rollout` with:
- subCommand: "undo"
- resourceType: "deployment"
- name: "myashes-backend"
- namespace: "myashes-backend"
- revision: (optional, specify if user wants specific revision)

### 4. Verify Rollback

Use `mcp__kubernetes__kubectl_rollout` with:
- subCommand: "status"
- resourceType: "deployment"
- name: "myashes-backend"
- namespace: "myashes-backend"

### 5. Health Check

```bash
curl -s -w "\nHTTP Status: %{http_code}\n" https://artemis.hq.solidrust.net/api/v1/builds?limit=1 | head -c 200
```

## Report

- Previous revision number
- New (rolled back) revision number
- Pod status after rollback
- API health status
