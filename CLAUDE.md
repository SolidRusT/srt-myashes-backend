# CLAUDE.md - Ashes of Creation Assistant Backend

**Project**: Community backend for Ashes of Creation game assistant
**Status**: v2.0 DEPLOYED AND LIVE
**Visibility**: PUBLIC (community collaboration)
**Last Updated**: 2026-01-14
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
ashes-of-creation-assistant/
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

### Backlog (Updated 2026-01-14)

| Item | Priority | Effort | Notes |
|------|----------|--------|-------|
| Build templates | LOW | 2-4 hrs | Pre-made builds for Tank, Healer, DPS playstyles |
| Popular builds widget | LOW | 2-4 hrs | Show trending builds on homepage (data exists) |
| Build search/filter | MEDIUM | 4-8 hrs | Search by name, tags, description |
| AoC data connector | MEDIUM | 30-54 hrs | Migrate data-pipeline/ to srt-data-layer (spike first) |
| Discord bot | MEDIUM | 16-24 hrs | `/build`, `/craft`, `/ask` commands |
| Rate limiting | LOW | 2-4 hrs | Add slowapi if abuse detected |
| User profiles | HIGH | 24-40 hrs | Needs auth system (currently session-only) |
| Economy tracker | HIGH | 40+ hrs | **BLOCKED** - No official API yet |

### AoC Data Connector Migration Details

**What exists**: 3 scrapers targeting [Ashes Wiki](https://ashesofcreation.wiki/), [Ashes Codex](https://ashescodex.com/), and [official site](https://ashesofcreation.com/)

**Complexity factors**:
- Playwright browser automation (may need architecture adaptation)
- Milvus vector DB (srt-data-layer may use different backend)
- Incremental state tracking (file-based → distributed)
- ~300MB embedding model (BAAI/bge-large-en-v1.5)

**Recommendation**: Spike first - prototype single scraper in srt-data-layer to validate patterns.

### Game Status Context

- **AoC is in Early Access** on Steam since Dec 11, 2025
- **No official API** - Intrepid still "considering" API design
- **~70-80% core gameplay** implemented, content still being added
- **Beta expected** late 2026, full release late 2026 / early 2027
- Many features may be premature until game stabilizes

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
| 2026-01-14 | **v2.0 COMPLETE** | Archived initial implementation, docs cleanup |
| 2026-01-14 | Prometheus metrics added | Full observability via Grafana |
| 2026-01-14 | K8s deployment complete | All endpoints live via Artemis |
| 2026-01-14 | Initial implementation | Builds, Feedback, Analytics APIs |

---

## Claude Code Configuration

**Commands** (`.claude/commands/`):
- No custom commands configured yet

**MCP Tools** (`.mcp.json`):
- `time` - Date calculations
- `calculator` - Math operations
- `github` - PR/issue management
- `gitea` - Gitea PR/issue management

---

**Last Updated**: 2026-01-14
**Status**: v2.0 DEPLOYED AND LIVE with full observability
**Next Steps**: Research new features, groom backlog, create next implementation plan

---

*This is a PUBLIC repository for community collaboration. Sensitive platform details are in private repos.*
