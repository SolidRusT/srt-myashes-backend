# /deploy - Build and Deploy MyAshes Backend

Build a new Docker image and deploy to Kubernetes.

## Pre-flight Checks

1. Verify working directory is clean:
   ```bash
   git status --short
   ```

2. Ensure on main branch or confirm deployment branch with user.

## Build Steps

1. **Build Docker image**:
   ```bash
   docker build -t poseidon.hq.solidrust.net:30008/shaun/myashes-backend:latest -f backend/Dockerfile backend/
   ```

2. **Push to Gitea registry**:
   ```bash
   docker push poseidon.hq.solidrust.net:30008/shaun/myashes-backend:latest
   ```

3. **Rollout restart**:
   ```bash
   kubectl rollout restart deployment/myashes-backend -n myashes-backend
   ```

4. **Wait for rollout**:
   ```bash
   kubectl rollout status deployment/myashes-backend -n myashes-backend --timeout=120s
   ```

5. **Verify health**:
   ```bash
   kubectl get pods -n myashes-backend -l app=myashes-backend
   curl -s https://artemis.hq.solidrust.net/api/v1/builds?limit=1 | head -c 100
   ```

## On Failure

- Check pod logs: `kubectl logs -l app=myashes-backend -n myashes-backend --tail=50`
- Check events: `kubectl get events -n myashes-backend --sort-by='.lastTimestamp' | tail -20`
