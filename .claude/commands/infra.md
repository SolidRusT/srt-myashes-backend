# /infra - Spawn Infrastructure Agent

Spawn a sub-agent to work in the srt-hq-k8s repository (Kubernetes infrastructure).

## Repository Details

- **Path**: `/Users/shaun/repos/srt-hq-k8s/`
- **Purpose**: Kubernetes cluster configuration and infrastructure
- **Tech**: K8s manifests, Helm charts, ArgoCD, monitoring stack
- **Manages**: All SRT services including myashes-backend

## Instructions

Use the **Task tool** to spawn a general-purpose sub-agent with:

```
subagent_type: "general-purpose"
prompt: |
  You are working in the srt-hq-k8s repository at /Users/shaun/repos/srt-hq-k8s/

  IMPORTANT: First read the CLAUDE.md file at /Users/shaun/repos/srt-hq-k8s/CLAUDE.md
  to understand the cluster structure, namespaces, and conventions.

  Your task: $ARGUMENTS

  After completing the task, provide a summary of:
  - What was done
  - Manifests modified
  - Any kubectl commands needed to apply changes
  - Impact on myashes-backend or other services
```

Replace `$ARGUMENTS` with the user's request.

## Common Tasks

- Update Kubernetes manifests
- Modify KEDA scaling rules
- Update Prometheus/Grafana dashboards
- Configure new services
- Update Artemis proxy routes
- Manage secrets and configmaps

## MyAshes Infrastructure

Key resources for myashes-backend:
- Namespace: `myashes-backend`
- Deployment: `myashes-backend` (6 replicas, KEDA 0-10)
- Service: ClusterIP on port 8000
- ServiceMonitor: `myashes-backend` in monitoring namespace
- Database: `platform-postgres` in `data-platform` namespace

## Example Usage

User: "/infra Update the KEDA scaling threshold to scale at 50 requests/sec"

Spawn agent with task to modify the ScaledObject, noting the current configuration.
