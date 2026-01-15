# /metrics - View MyAshes Backend Metrics

Fetch and display Prometheus metrics for the myashes-backend service.

## Available Metrics

The backend exposes these metrics via `/metrics` endpoint:
- `http_requests_total` - Request count by method/status/handler
- `http_request_duration_seconds` - Latency histogram
- `http_request_size_bytes` / `http_response_size_bytes`
- `myashes_http_requests_inprogress` - Active requests gauge

## Instructions

### Option 1: Direct Metrics Endpoint

Fetch raw metrics from a pod:

```bash
kubectl exec -n myashes-backend deploy/myashes-backend -- wget -qO- http://localhost:8000/metrics 2>/dev/null | grep -E "^(http_requests|myashes)" | head -30
```

### Option 2: Prometheus Query (if available)

Common PromQL queries:

1. **Request rate (last 5m)**:
   ```
   rate(http_requests_total{kubernetes_namespace="myashes-backend"}[5m])
   ```

2. **Error rate**:
   ```
   rate(http_requests_total{kubernetes_namespace="myashes-backend",status=~"5.."}[5m])
   ```

3. **P95 latency**:
   ```
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{kubernetes_namespace="myashes-backend"}[5m]))
   ```

### Option 3: Pod Resource Usage

Use `mcp__kubernetes__kubectl_generic` with:
- command: "top"
- resourceType: "pod"
- namespace: "myashes-backend"
- labelSelector: "app=myashes-backend"

## Report Format

Summarize:
- Total requests served
- Error rate percentage
- Average/P95 latency
- Current pod CPU/memory usage
- Any anomalies or concerns
