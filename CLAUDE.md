# CLAUDE.md - Ashes of Creation Assistant Backend

**Project**: Community backend for Ashes of Creation game assistant
**Status**: DEPLOYED AND LIVE - All Phase 1-7 Complete
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
├── data-pipeline/                # TO MIGRATE to srt-data-layer
└── CLAUDE.md                     # This file
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

## Implementation Status

### Completed Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Delete redundant code | ✅ COMPLETE |
| 2 | Builds API (CRUD + voting) | ✅ COMPLETE |
| 3 | Feedback API | ✅ COMPLETE |
| 4 | Analytics API | ✅ COMPLETE |
| 6 | Database + Config | ✅ COMPLETE |
| 7 | K8s Deployment + Artemis | ✅ COMPLETE |

### Remaining Work

| Phase | Description | Priority |
|-------|-------------|----------|
| 5 | Rate limiting | LOW - can add later |
| 8 | AoC connector migration | SEPARATE EFFORT |

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
| 2026-01-14 | **DEPLOYED TO K8S** | All endpoints live via Artemis |
| 2026-01-14 | Phase 7 complete | K8s deployment, Artemis routing, DB permissions |
| 2026-01-14 | Phase 4 complete | Analytics API (search recording, popular queries) |
| 2026-01-14 | Phase 3 complete | Feedback API (thumbs up/down) |
| 2026-01-14 | Phase 2 complete | Builds API (CRUD + voting) |
| 2026-01-14 | Phase 1 complete | Deleted redundant code (15 files) |
| 2026-01-14 | Discovery complete | Identified refactoring needs |

---

**Last Updated**: 2026-01-14
**Status**: DEPLOYED AND LIVE
**Next Steps**: Frontend integration testing, then Phase 5 (rate limiting) if needed

---

*This is a PUBLIC repository for community collaboration. Sensitive platform details are in private repos.*
