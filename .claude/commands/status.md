# /status - Check MyAshes Backend Health

Check the deployment status and health of the myashes-backend service.

## Steps

1. **Check pod status**:
   ```bash
   kubectl get pods -n myashes-backend -l app=myashes-backend
   ```

2. **Check deployment rollout status**:
   ```bash
   kubectl rollout status deployment/myashes-backend -n myashes-backend --timeout=10s
   ```

3. **Check recent events** (for errors):
   ```bash
   kubectl get events -n myashes-backend --sort-by='.lastTimestamp' | tail -10
   ```

4. **Check endpoint health** via Artemis:
   ```bash
   curl -s https://artemis.hq.solidrust.net/api/v1/builds?limit=1 | head -c 200
   ```

5. **Report any issues found** with recommended actions.
