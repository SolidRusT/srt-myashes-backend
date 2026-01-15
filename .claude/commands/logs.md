# /logs - View MyAshes Backend Logs

View recent logs from the myashes-backend pods, with optional error filtering.

## Basic Logs

```bash
kubectl logs -l app=myashes-backend -n myashes-backend --tail=100 --all-containers=true
```

## Error-Focused Logs

```bash
kubectl logs -l app=myashes-backend -n myashes-backend --tail=200 | grep -iE "(error|exception|traceback|failed|critical)" | tail -50
```

## Follow Logs (Live)

```bash
kubectl logs -l app=myashes-backend -n myashes-backend --tail=20 -f
```
(Use Ctrl+C to stop)

## Specific Pod Logs

If you need logs from a specific pod:
```bash
kubectl get pods -n myashes-backend -l app=myashes-backend -o name | head -1 | xargs kubectl logs -n myashes-backend --tail=100
```

## Report Summary

After viewing logs, summarize:
- Any errors or exceptions found
- Request patterns (if visible)
- Recommended actions if issues detected
