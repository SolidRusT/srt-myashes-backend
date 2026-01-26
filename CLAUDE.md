# CLAUDE.md - srt-myashes-backend

**Project**: Product-specific backend for MyAshes.ai game assistant
**Status**: v2.0 DEPLOYED AND LIVE
**Visibility**: PUBLIC (community collaboration)
**Last Updated**: 2026-01-15
**Shaun's Golden Rule**: **No workarounds, no temporary fixes, no disabled functionality. Full solutions only.**

---

## CRITICAL: READ THIS FIRST

**Backend is LIVE as of 2026-01-14.** All core APIs deployed and working via Artemis.

This repo provides **product-specific backend services** for MyAshes.ai:
- **LIVE**: Build persistence, voting, feedback collection, search analytics
- **DELETED**: Chat/RAG, vector store, embeddings, LLM service, JWT auth
- **PENDING**: Rate limiting (Phase 5), AoC data connector migration (Phase 8)

**Live Endpoints** (via `https://artemis.hq.solidrust.net`):
- `GET/POST /api/v1/builds` - Build CRUD
- `DELETE /api/v1/builds/{id}` - Delete build (owner only)
- `POST /api/v1/builds/{id}/vote` - Vote 1-5
- `POST /api/v1/feedback` - AI response feedback
- `POST /api/v1/analytics/search` - Record search
- `GET /api/v1/analytics/popular-queries` - Popular queries

**Frontend uses srt-data-layer directly** (routed via `/data/*`):
- `/data/v1/agent/chat` - Chat with RAG
- `/data/v1/query/semantic` - Vector search
- `/data/v1/query/keyword` - Keyword search

---

## Architecture (DEPLOYED)

```
┌─────────────────────────────────────────────────────────────┐
│  myashes.ai (Frontend)                                       │
│  - Static site on GitHub Pages                               │
│  - Uses ES6 modules, localStorage for client state           │
│  - LIVE with AI chat + build sharing                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Artemis Proxy (https://artemis.hq.solidrust.net)           │
│  - Routes /data/* → srt-data-layer                          │
│  - Routes /api/*  → THIS BACKEND ✅ CONFIGURED              │
│  - CORS for myashes.ai + X-Session-ID header                │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌─────────────────────┐   ┌─────────────────────────────────┐
│  srt-data-layer     │   │  THIS REPO                      │
│  (Shared Platform)  │   │  ✅ DEPLOYED TO K8S             │
│  ✅ DEPLOYED        │   │                                 │
│                     │   │  Live endpoints:                │
│  Already provides:  │   │  - /api/v1/builds/*             │
│  - /data/v1/query/* │   │  - /api/v1/feedback             │
│  - /data/v1/agent/* │   │  - /api/v1/analytics/*          │
│  - Vector search    │   │                                 │
│  - Knowledge graph  │   │  6 pods running                 │
└─────────────────────┘   │  PostgreSQL: platform-postgres  │
                          │  Cache: Valkey                  │
                          └─────────────────────────────────┘
```

---

## Deployment Details

### Kubernetes Resources
- **Namespace**: `myashes-backend`
- **Deployment**: 6 replicas, auto-scaling via KEDA (0-10)
- **Image**: `poseidon.hq.solidrust.net:30008/shaun/myashes-backend:latest`
- **Registry Secret**: `gitea-registry` (for Gitea container registry)

### Database
- **Host**: `platform-postgres-rw.data-platform.svc.cluster.local`
- **Database**: `myashes`
- **User**: `myashes`
- **Tables**: `builds`, `build_votes`, `feedback`, `search_analytics`, `alembic_version`

### Cache
- **Host**: `valkey.data-platform.svc.cluster.local:6379`

### Artemis Configuration
- **Upstream**: `aoc_backend` → `myashes-backend.hq.solidrust.net:8086`
- **Location**: `/api/*` with CORS for myashes.ai
- **Headers**: `X-Session-ID` exposed in CORS

### Observability
- **Prometheus**: `/metrics` endpoint via `prometheus-fastapi-instrumentator`
- **ServiceMonitor**: `myashes-backend` in `monitoring` namespace (srt-hq-k8s)
- **Metrics collected**:
  - `http_requests_total` - Request count by method/status/handler
  - `http_request_duration_seconds` - Latency histogram
  - `http_request_size_bytes` / `http_response_size_bytes`
  - `myashes_http_requests_inprogress` - Active requests gauge
  - Python runtime metrics (GC, process memory, CPU)

---

## Project Structure (Current)

```
srt-myashes-backend/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── __init__.py       # Router registration
│   │   │   ├── builds.py         # Build CRUD + voting
│   │   │   ├── feedback.py       # AI response feedback
│   │   │   └── analytics.py      # Search analytics
│   │   ├── core/
│   │   │   ├── config.py         # Settings (DB, Redis, CORS)
│   │   │   ├── errors.py         # Custom exceptions
│   │   │   ├── security.py       # ID generators
│   │   │   └── session.py        # Session middleware
│   │   ├── db/
│   │   │   ├── base.py           # Model imports
│   │   │   ├── base_class.py     # Base model class
│   │   │   └── session.py        # DB session factory
│   │   ├── game_constants/
│   │   │   └── game_data.py      # CLASS_MATRIX, RACES, ARCHETYPES
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── build.py          # Build + BuildVote models
│   │   │   ├── feedback.py       # Feedback model
│   │   │   └── analytics.py      # SearchAnalytics model
│   │   ├── schemas/
│   │   │   ├── builds.py         # Build Pydantic schemas
│   │   │   ├── feedback.py       # Feedback schemas
│   │   │   └── analytics.py      # Analytics schemas
│   │   └── main.py               # FastAPI app
│   ├── migrations/
│   │   └── versions/
│   │       ├── 001_create_builds_tables.py
│   │       ├── 002_create_feedback_table.py
│   │       └── 003_create_search_analytics_table.py
│   ├── Dockerfile                # python:3.10-slim based
│   ├── entrypoint.sh             # Wait for DB, run migrations, start app
│   └── requirements.txt          # Slimmed dependencies
├── k8s/
│   ├── 00-namespace.yaml
│   ├── 02-configmap.yaml
│   ├── 03-secret.yaml            # Template only - real secret in K8s
│   ├── 04-deployment.yaml
│   ├── 05-service.yaml
│   ├── 07-migration-job.yaml
│   └── 08-keda-scaledobject.yaml
├── .github/workflows/
│   └── ci-cd.yml                 # Backend-only CI (lint, test, build)
├── data-pipeline/                # TO MIGRATE to srt-data-layer (Phase 8)
├── CLAUDE.md                     # This file (source of truth)
└── README.md                     # Project overview
```

---

## API Reference

### Builds

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/builds` | List builds (paginated, filterable) |
| POST | `/api/v1/builds` | Create new build |
| GET | `/api/v1/builds/{id}` | Get build by ID |
| PATCH | `/api/v1/builds/{id}` | Update build (owner only) |
| DELETE | `/api/v1/builds/{id}` | Delete build (owner only) |
| POST | `/api/v1/builds/{id}/vote` | Vote on build (1-5) |

### Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/feedback` | Submit AI response feedback |

**Payload**:
```json
{
  "query": "search query",
  "response_snippet": "AI response text",
  "rating": "up" | "down",
  "search_mode": "quick" | "smart" | "deep",
  "comment": "optional"
}
```

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analytics/search` | Record search query |
| GET | `/api/v1/analytics/popular-queries` | Get popular queries |

**Search Payload**:
```json
{
  "query": "search query",
  "search_mode": "quick" | "smart" | "deep",
  "result_count": 5
}
```

### Session Handling
- Send `X-Session-ID` header with requests
- If missing, backend generates one and returns in response header
- Session format: `sess_` + 24 hex chars

### Error Response Format
```json
{
  "error": "error_code",
  "message": "Human readable message",
  "status": 404
}
```

---

## Current Status

**Backend v2.0 is COMPLETE and LIVE.** All core functionality deployed and monitored.

## Issue Tracking

**Platform**: GitHub
**Issues**: https://github.com/SolidRusT/srt-myashes-backend/issues

Backlog, bugs, and enhancements are tracked as GitHub issues.
This CLAUDE.md contains domain knowledge and patterns, not task tracking.

**To check current work**: Review open issues
**To add new work**: Create an issue with acceptance criteria

### Key Context

- **Authentication Strategy**: Steam Login via PAM Platform (anonymous read, authenticated write)
- **Game Status**: AoC is in Early Access (Dec 2025), no official API yet
- **Data Quality**: Users report some AI inaccuracies - see AI Data Quality Dashboard issue

---

## Archive: Initial Implementation (2026-01-14)

<details>
<summary>Click to expand completed phases</summary>

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Delete redundant code (15 files) | ✅ COMPLETE |
| 2 | Builds API (CRUD + voting) | ✅ COMPLETE |
| 3 | Feedback API | ✅ COMPLETE |
| 4 | Analytics API | ✅ COMPLETE |
| 5 | Rate limiting | ⏸️ SKIPPED (low priority) |
| 6 | Database + Config | ✅ COMPLETE |
| 7 | K8s Deployment + Artemis | ✅ COMPLETE |
| - | Prometheus observability | ✅ COMPLETE |

</details>

---

## Frontend Integration Status

**Message sent to frontend agent 2026-01-14:**

```
Backend deployment complete. All endpoints live via Artemis.

ENDPOINTS AVAILABLE:
- GET  /api/v1/builds           - List builds (paginated)
- POST /api/v1/builds           - Create build
- GET  /api/v1/builds/{id}      - Get build by ID
- PATCH /api/v1/builds/{id}     - Update build
- DELETE /api/v1/builds/{id}    - Delete build (owner only)
- POST /api/v1/builds/{id}/vote - Vote on build (up/down)
- POST /api/v1/feedback         - Submit AI feedback (thumbs up/down)
- POST /api/v1/analytics/search - Record search analytics
- GET  /api/v1/analytics/popular-queries - Get popular queries

BASE URL: https://artemis.hq.solidrust.net

SESSION TRACKING:
- Send X-Session-ID header with requests
- Header is exposed in CORS responses

SEARCH MODES (for feedback/analytics):
- "quick", "smart", "deep"

Ready for frontend integration.
```

---

## Development Commands

```bash
# Local development
cd backend
source .venv/bin/activate  # or: uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload

# Build and push Docker image
docker build -t poseidon.hq.solidrust.net:30008/shaun/myashes-backend:latest -f backend/Dockerfile backend/
docker push poseidon.hq.solidrust.net:30008/shaun/myashes-backend:latest

# K8s deployment
kubectl apply -f k8s/
kubectl rollout restart deployment/myashes-backend -n myashes-backend

# Check pod logs
kubectl logs -l app=myashes-backend -n myashes-backend --tail=50

# Database access (if needed)
kubectl exec -it platform-postgres-3 -n data-platform -- psql -U postgres -d myashes
```

---

## Related Repositories

| Resource | Location | Purpose |
|----------|----------|---------|
| **Frontend** | `/Users/shaun/repos/myashes.github.io/` | Live at myashes.ai |
| **Data Layer** | `/Users/shaun/repos/srt-data-layer/` | RAG/vector platform |
| **K8s Platform** | `/Users/shaun/repos/srt-hq-k8s/` | Infrastructure |
| **Artemis** | `/Users/shaun/repos/srt-inference-proxy/` | API gateway |

---

## User Preferences (CRITICAL)

### Shaun's Rules
- ✅ **Complete, working solutions** - Every change must be deployable
- ✅ **No workarounds** - Fix root causes, not symptoms
- ✅ **Git as source of truth** - All changes in code
- ✅ **Documentation first** - Update CLAUDE.md with findings
- ❌ **NO temporary fixes**
- ❌ **NO disabled functionality**

### Container Registry
- **Primary**: Gitea at `poseidon.hq.solidrust.net:30008`
- **Token**: `GITEA_TOKEN` in `~/.zshrc`
- **K8s Secret**: `gitea-registry` in `myashes-backend` namespace

---

## Change History

| Date | Change | Impact |
|------|--------|--------|
| 2026-01-15 | Claude Code commands expanded | 9 slash commands, 5 MCP tools, agent delegation |
| 2026-01-14 | **v2.0 COMPLETE** | Archived initial implementation, docs cleanup |
| 2026-01-14 | Prometheus metrics added | Full observability via Grafana |
| 2026-01-14 | K8s deployment complete | All endpoints live via Artemis |
| 2026-01-14 | Initial implementation | Builds, Feedback, Analytics APIs |

---

## Claude Code Configuration

### Slash Commands (`.claude/commands/`)

**Operational Commands** - Use Kubernetes MCP tools directly:

| Command | Description |
|---------|-------------|
| `/status` | Check deployment health, pod status, events, and API health |
| `/deploy` | Build Docker image, push to Gitea registry, rollout to K8s |
| `/logs` | View recent pod logs with error filtering |
| `/rollback` | Roll back deployment to previous revision |
| `/db` | Check database connectivity, run read-only queries |
| `/metrics` | View Prometheus metrics and pod resource usage |

**Agent Commands** - Spawn sub-agents in related repositories:

| Command | Description |
|---------|-------------|
| `/frontend` | Spawn agent in `myashes.github.io` for frontend tasks |
| `/data-layer` | Spawn agent in `srt-data-layer` for RAG/vector platform tasks |
| `/infra` | Spawn agent in `srt-hq-k8s` for infrastructure tasks |

Agent commands preserve context in the current session while delegating work to specialized repositories. Each agent reads the target repo's CLAUDE.md and executes the specified task.

### MCP Tools (`.mcp.json`)

| Tool | Purpose |
|------|---------|
| `kubernetes` | Direct K8s cluster access (kubectl via MCP, no bash needed) |
| `github` | GitHub PR/issue management |
| `gitea` | Gitea PR/issue management for poseidon registry |
| `time` | Date/time calculations |
| `calculator` | Math operations |

### Tool Preferences

- **Prefer MCP tools over Bash** for Kubernetes operations - more reliable, no permission prompts
- Use `mcp__kubernetes__kubectl_get`, `kubectl_logs`, `kubectl_rollout` instead of bash kubectl
- Reserve Bash for: Docker builds, curl health checks, git operations

---

**Last Updated**: 2026-01-15
**Status**: v2.0 DEPLOYED AND LIVE with full observability
**Next Steps**: Research new features, groom backlog, create next implementation plan

---

*This is a PUBLIC repository for community collaboration. Sensitive platform details are in private repos.*

## MCP Tool Usage (ToolSearch Required)

With deferred tool loading enabled, MCP tools DO NOT EXIST until loaded via ToolSearch.

**You MUST call ToolSearch FIRST before using ANY MCP tool.**

```
WRONG: Try to call mcp__gitea__create_issue directly -> "No such tool available" error
RIGHT: ToolSearch("select:mcp__gitea__create_issue") -> tool loads -> call mcp__gitea__create_issue
```

**Pattern:**
1. `ToolSearch(query="select:mcp__gitea__create_issue")` - loads the tool
2. Call the tool - now it exists

If you don't know the exact name, use keyword search: `ToolSearch(query="+gitea issue")`

Available MCP servers: calculator, gitea, kubernetes, time