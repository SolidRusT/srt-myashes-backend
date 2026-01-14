# CLAUDE.md - Ashes of Creation Assistant Backend

**Project**: Community backend for Ashes of Creation game assistant
**Status**: Phase 4 COMPLETE - All APIs implemented, ready for deployment
**Visibility**: PUBLIC (community collaboration)
**Last Updated**: 2026-01-14
**Shaun's Golden Rule**: **No workarounds, no temporary fixes, no disabled functionality. Full solutions only.**

---

## CRITICAL: READ THIS FIRST

**Phase 1 completed 2026-01-14.** Codebase cleaned, ready for feature implementation.

This repo provides **product-specific backend services** for MyAshes.ai:
- **PROVIDES**: Build persistence, voting, feedback collection, search analytics
- **DELETED**: Chat/RAG, vector store, embeddings, LLM service, JWT auth, Discord bot
- **PENDING**: Data pipeline scrapers → srt-data-layer as AoC connector

**Frontend Requirements Document**: `/Users/shaun/repos/myashes.github.io/docs/BACKEND-REQUIREMENTS.md`

The platform provides via **srt-data-layer** (routed via `/data/*`):
- `/data/v1/agent/chat` - Chat with tool-calling and RAG
- `/data/v1/query/semantic` - Vector search via Milvus
- `/data/v1/query/keyword` - Full-text search via MeiliSearch
- `/data/v1/query/knowledge-graph` - Neo4j entity queries
- `/data/v1/connectors/*` - Data ingestion infrastructure

---

## Strategic Context (Post-Refactoring)

```
┌─────────────────────────────────────────────────────────────┐
│  myashes.ai (Frontend)                                       │
│  - Static site on GitHub Pages                               │
│  - Uses ES6 modules, localStorage for client state           │
│  - Already LIVE with AI chat via Artemis                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Artemis Proxy (https://artemis.hq.solidrust.net)           │
│  - Routes /data/* → srt-data-layer (generic platform)       │
│  - Routes /api/*  → ashes-of-creation-assistant (product)   │
│  - Handles CORS for myashes.ai                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌─────────────────────┐   ┌─────────────────────────────────┐
│  srt-data-layer     │   │  THIS REPO (refactored)         │
│  (Shared Platform)  │   │  (Product-Specific Backend)     │
│  ✅ DEPLOYED        │   │  ⚠️ IMPLEMENTATION IN PROGRESS  │
│                     │   │                                 │
│  Already provides:  │   │  Will provide:                  │
│  - /data/v1/query/* │   │  - /api/v1/builds/*             │
│  - /data/v1/ingest/*│   │  - /api/v1/feedback/*           │
│  - /data/v1/agent/* │   │  - /api/v1/analytics/*          │
│  - Vector search    │   │  - Session management           │
│  - Knowledge graph  │   │  - Build persistence + voting   │
│    └─ AoC connector │   │                                 │
│       (TO BE ADDED) │   │  PostgreSQL-backed              │
└─────────────────────┘   └─────────────────────────────────┘
```

---

## Discovery Checklist (COMPLETED 2026-01-14)

### 1. What does this repo currently provide?
- [x] **API Endpoints** (`backend/app/api/v1/`):
  - `auth/router.py` - JWT auth: register, login, refresh, password reset
  - `users/router.py` - Profile, preferences, subscription management
  - `builds.py` - Character build CRUD, archetypes, classes, races (uses vector_store)
  - `chat.py` - Chat completions with RAG context (uses vector_store + LLM service)
  - `items.py` - Item database search (uses vector_store)
  - `crafting.py` - Recipes, professions, crafting calculator (uses vector_store)
  - `servers.py` - Game server status, economy data
  - `locations.py` - Zones, resources, POIs (uses vector_store)

- [x] **Services** (`backend/app/services/`):
  - `vector_store.py` - Own Milvus connection + SentenceTransformer embeddings ❌ REDUNDANT
  - `llm_service.py` - OpenAI-compatible API with RAG ❌ REDUNDANT
  - `cache_service.py` - Redis caching ✅ KEEP (for user sessions)
  - `email.py` - SMTP email service ✅ KEEP

- [x] **Database Models** (`backend/app/models/`):
  - `User` - email, username, premium status, created_at ✅ KEEP
  - `UserPreference` - notifications, UI settings ✅ KEEP
  - `SavedItem` - user's favorited game items ✅ KEEP
  - `Build` - character builds (JSON data in PostgreSQL) ✅ KEEP

- [x] **Data Pipeline** (`data-pipeline/`):
  - Wiki scraper (ashesofcreation.wiki) using Playwright
  - Codex scraper
  - Official website scraper
  - Game files processor
  - Vector indexer with SentenceTransformer
  - Chunk processor
  - → **MIGRATE** to srt-data-layer as AoC connector

### 2. What's now handled by srt-data-layer?
- [x] **Vector search** - `/v1/query/semantic` with Milvus + BAAI/bge-m3 embeddings
- [x] **Keyword search** - `/v1/query/keyword` with MeiliSearch
- [x] **RAG chat** - `/v1/agent/chat` with tool-calling via srt-tool-agents-lite
- [x] **Knowledge graph** - `/v1/query/knowledge-graph` with Neo4j
- [x] **Embedding generation** - vLLM embeddings service (centralized)
- [x] **Data ingestion** - `/v1/ingest/*` with deduplication, chunking
- [x] **Data hygiene** - `/v1/hygiene/*` for dedup and cleanup

### 3. What's still needed from this repo? (REVISED per frontend requirements)
- [ ] ~~**User authentication**~~ - ❌ NOT NEEDED Phase 1 (session-based instead)
- [ ] ~~**User accounts**~~ - ❌ NOT NEEDED Phase 1 (OAuth Phase 2)
- [x] **Build persistence** - PostgreSQL CRUD with voting ✅ REQUIRED
- [x] **Build sharing** - Public builds with share URLs ✅ REQUIRED
- [ ] ~~**Saved items**~~ - ❌ NOT IN FRONTEND REQUIREMENTS
- [x] **Response feedback** - Thumbs up/down on AI responses ✅ NEW
- [x] **Search analytics** - Query logging + popular queries ✅ NEW
- [x] **Session management** - Anonymous session tracking ✅ NEW
- [x] **Rate limiting** - Per-endpoint limits ✅ REQUIRED

### 4. What should move TO srt-data-layer?
- [x] **Data pipeline scrapers** → Create AoC connector in srt-data-layer
- [x] **Embedding logic** → Already centralized in vLLM embeddings
- [x] **Vector indexing** → Use `/v1/ingest/*` endpoints

---

## Integration Requirements

When this backend is deployed, it must use:

### Platform Services (srt-hq-k8s)
- **PostgreSQL**: CNPG cluster for relational data (users, builds)
- **Artemis**: Proxy for frontend integration
- **KEDA**: Auto-scaling based on load
- **FluxCD**: GitOps deployment

### Shared Data Layer (srt-data-layer)
- **DO NOT** implement your own vector search
- **DO NOT** implement your own embedding generation
- **DO NOT** implement your own RAG
- **INSTEAD** call srt-data-layer APIs for all knowledge base operations

### Frontend Integration (myashes.ai)
- All endpoints must be accessible via Artemis proxy
- CORS must be configured for myashes.ai origin
- Response formats must match frontend expectations

**Agreed Integration Details (2026-01-14):**

| Item | Decision |
|------|----------|
| Session ID format | `sess_` + 24 hex chars (frontend generates) |
| Session header | `X-Session-ID` on all requests |
| Build ID format | `b_` + 8 hex chars (backend generates) |
| Share URL format | `https://myashes.ai/?build={build_id}` (GitHub Pages limitation) |
| Error response | `{"error": "code", "message": "text", "status": 404}` |

**Frontend Reference**: `/Users/shaun/repos/myashes.github.io/docs/BACKEND-INTEGRATION.md`

**Error Codes to Implement:**
- `build_not_found` (404)
- `validation_error` (400)
- `already_voted` (409)
- `rate_limited` (429)
- `not_implemented` (501)
- `internal_error` (500)

**Answers to Frontend Questions (2026-01-14):**

1. **Artemis `/api/*` routing**: NOT YET configured. Pending Phase 7 (K8s deployment). NGINX config template is ready in this CLAUDE.md. Frontend can test locally with direct backend calls until then.

2. **Session validation**: Backend will be lenient:
   - If `X-Session-ID` header present → use it
   - If missing → generate new session ID, return in `X-Session-ID` response header
   - Frontend should capture returned header and store if it generated a request without one
   - This enables graceful degradation and easier testing

3. **Build deletion**: YES, adding to Phase 2 scope:
   - `DELETE /api/v1/builds/{build_id}` - Delete a build
   - Only the session that created the build can delete it
   - Returns `403 Forbidden` with `not_owner` error code if session doesn't match

---

## Related Repositories

| Resource | Location | Purpose |
|----------|----------|---------|
| **Frontend** | `/Users/shaun/repos/myashes.github.io/` | Live at myashes.ai |
| **Data Layer** | `/Users/shaun/repos/srt-data-layer/` | RAG/vector platform |
| **K8s Platform** | `/Users/shaun/repos/srt-hq-k8s/` | Infrastructure |
| **Artemis** | `/Users/shaun/repos/srt-inference-proxy/` | API gateway |

---

## Project Structure (After Phase 1 Cleanup)

```
ashes-of-creation-assistant/
├── backend/                   # FastAPI backend (CLEANED)
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── builds.py      # Stub - implement in Phase 2
│   │   ├── core/
│   │   │   ├── config.py          # Simplified config (no Milvus/JWT)
│   │   │   └── security.py        # Session ID generators
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── base_class.py
│   │   │   └── session.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── build.py           # Updated for frontend spec
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── cache_service.py   # Redis caching
│   │   └── main.py                # FastAPI app entry point
│   ├── .venv/                     # uv virtual environment
│   ├── migrations/                # Alembic migrations (needs update)
│   └── requirements.txt           # Slimmed dependencies (25 packages)
├── frontend/                  # NOT USED - myashes.github.io instead
├── data-pipeline/             # TO MIGRATE to srt-data-layer
├── k8s/                       # NEEDS UPDATE for KEDA + FluxCD
├── Dockerfile                 # NEEDS UPDATE for slimmer image
└── CLAUDE.md                  # This file
```

---

## Current State Assessment (REVISED 2026-01-14)

### API Endpoints - Action Required:

| Current Endpoint | Purpose | Action | Notes |
|------------------|---------|--------|-------|
| `/v1/auth/*` | JWT authentication | ❌ DELETE | Frontend uses session-based auth (Phase 1) |
| `/v1/users/*` | User profiles/prefs | ❌ DELETE | Not needed for Phase 1, OAuth comes later |
| `/v1/builds/*` | Build CRUD | 🔄 REFACTOR | Rewrite to match frontend spec, add voting |
| `/v1/chat/*` | RAG chat | ❌ DELETE | Frontend calls srt-data-layer directly |
| `/v1/items/*` | Item search | ❌ DELETE | Frontend calls srt-data-layer directly |
| `/v1/crafting/*` | Recipe search | ❌ DELETE | Frontend calls srt-data-layer directly |
| `/v1/servers/*` | Server status | ❌ DELETE | Not in frontend requirements |
| `/v1/locations/*` | Zone/POI search | ❌ DELETE | Frontend calls srt-data-layer directly |

### New Endpoints - To Create:

| Endpoint | Purpose | Priority | Phase |
|----------|---------|----------|-------|
| `GET /api/v1/builds/{build_id}` | Get build by ID | **1** | Phase 2 |
| `POST /api/v1/builds` | Create build | **1** | Phase 2 |
| `GET /api/v1/builds` | List builds with filters | **2** | Phase 2 |
| `DELETE /api/v1/builds/{build_id}` | Delete build (owner only) | **2** | Phase 2 |
| `POST /api/v1/builds/{build_id}/vote` | Rate a build (1-5) | **3** | Phase 2 |
| `POST /api/v1/feedback` | AI response feedback | **4** | Phase 3 |
| `POST /api/v1/analytics/search` | Log search events | **5** | Phase 4 |
| `GET /api/v1/analytics/popular-queries` | Popular queries | **6** | Phase 4 |

### Services - Action Required:

| Service | Purpose | Action | Notes |
|---------|---------|--------|-------|
| `vector_store.py` | Milvus + embeddings | ❌ DELETE | srt-data-layer provides this |
| `llm_service.py` | OpenAI API + RAG | ❌ DELETE | srt-data-layer provides this |
| `cache_service.py` | Redis caching | ✅ KEEP | For popular queries cache |
| `email.py` | SMTP service | ❌ DELETE | Not needed for Phase 1 |

### Database Schema - New Tables:

```sql
-- Builds table (replaces existing)
CREATE TABLE builds (
    build_id VARCHAR(12) PRIMARY KEY,  -- e.g., "b_abc123"
    name VARCHAR(100) NOT NULL,
    description TEXT,
    primary_archetype VARCHAR(20) NOT NULL,
    secondary_archetype VARCHAR(20) NOT NULL,
    class_name VARCHAR(50) NOT NULL,  -- Computed from matrix
    race VARCHAR(20) NOT NULL,
    is_public BOOLEAN DEFAULT true,
    session_id VARCHAR(64),  -- For anonymous users
    user_id VARCHAR(64),     -- For authenticated users (future)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Build votes table (NEW)
CREATE TABLE build_votes (
    vote_id SERIAL PRIMARY KEY,
    build_id VARCHAR(12) REFERENCES builds(build_id),
    session_id VARCHAR(64),
    user_id VARCHAR(64),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(build_id, session_id),
    UNIQUE(build_id, user_id)
);

-- Feedback table (NEW)
CREATE TABLE feedback (
    feedback_id VARCHAR(12) PRIMARY KEY,
    query TEXT NOT NULL,
    response_snippet TEXT NOT NULL,
    search_mode VARCHAR(10) NOT NULL,
    rating VARCHAR(4) NOT NULL,  -- 'up' or 'down'
    comment TEXT,
    session_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Search analytics table (NEW)
CREATE TABLE search_analytics (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    search_mode VARCHAR(10) NOT NULL,
    result_count INTEGER,
    latency_ms INTEGER,
    sources_used TEXT[],
    session_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Materialized view for popular queries
CREATE MATERIALIZED VIEW popular_queries AS
SELECT
    query,
    COUNT(*) as count,
    DATE_TRUNC('day', created_at) as day
FROM search_analytics
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY query, DATE_TRUNC('day', created_at);
```

### Rate Limiting Requirements:

| Endpoint | Limit |
|----------|-------|
| `POST /api/v1/builds` | 10/min per session |
| `POST /api/v1/builds/{id}/vote` | 30/min per session |
| `POST /api/v1/feedback` | 20/min per session |
| `POST /api/v1/analytics/search` | 60/min per session |
| GET endpoints | 120/min per session |

### Data Pipeline Migration:

| Scraper | Target | Status |
|---------|--------|--------|
| `wiki_scraper.py` | srt-data-layer AoC connector | **TODO** - Create new connector |
| `codex_scraper.py` | srt-data-layer AoC connector | **TODO** - Create new connector |
| `official_website_scraper.py` | srt-data-layer AoC connector | **TODO** - Create new connector |
| `game_files_processor.py` | srt-data-layer AoC connector | **TODO** - Create new connector |

---

## Refactoring Plan (REVISED 2026-01-14)

### Phase 1: Delete Redundant Code ✅ COMPLETE

**Deleted Files (15 total):**
- API Routers: `chat.py`, `items.py`, `crafting.py`, `locations.py`, `servers.py`
- API Directories: `auth/`, `users/`
- Services: `vector_store.py`, `llm_service.py`, `email.py`
- Models/Schemas: `user.py`, `auth.py`, `users.py`
- CRUD: `users.py`
- Other: `discord_bot.py`, `config.py` (redundant)

**Updated Files:**
- `api/v1/__init__.py` - Only builds router remains
- `models/__init__.py` - Removed user imports
- `models/build.py` - Updated schema for frontend spec
- `api/v1/builds.py` - Stub returning 501 until Phase 2
- `core/config.py` - Removed JWT/Milvus/OpenAI settings
- `core/security.py` - Session ID generators instead of JWT
- `services/cache_service.py` - Fixed import path
- `db/base.py` - Removed user model imports
- `requirements.txt` - Reduced from 53 to 25 dependencies

**Verified:** Server starts, health endpoints respond correctly

### Phase 2: Implement Builds API ✅ COMPLETE

**Implemented 2026-01-14:**

| File | Purpose |
|------|---------|
| `core/errors.py` | Custom exceptions with agreed JSON format |
| `core/session.py` | Session middleware (extract or generate session ID) |
| `schemas/builds.py` | Pydantic schemas for all build operations |
| `data/game_data.py` | CLASS_MATRIX (64), RACES (9), ARCHETYPES (8) |
| `models/build.py` | Build + BuildVote SQLAlchemy models |
| `api/v1/builds.py` | Full CRUD + voting endpoints |
| `migrations/versions/001_create_builds_tables.py` | Database migration |

**Endpoints implemented:**
- `POST /api/v1/builds` - Create build
- `GET /api/v1/builds/{build_id}` - Get build
- `GET /api/v1/builds` - List with filters/pagination
- `DELETE /api/v1/builds/{build_id}` - Delete (owner only)
- `POST /api/v1/builds/{build_id}/vote` - Vote 1-5

**Verified:** Server starts, session IDs generated, all endpoints respond correctly

### Phase 3: Implement Feedback API ✅ COMPLETE

**Implemented 2026-01-14:**

| File | Purpose |
|------|---------|
| `schemas/feedback.py` | FeedbackCreate + FeedbackResponse Pydantic schemas |
| `models/feedback.py` | Feedback SQLAlchemy model |
| `api/v1/feedback.py` | POST endpoint for thumbs up/down |
| `migrations/versions/002_create_feedback_table.py` | Database migration |

**Endpoint implemented:**
- `POST /api/v1/feedback` - Submit feedback with rating (up/down) and optional comment

### Phase 4: Implement Analytics API ✅ COMPLETE

**Implemented 2026-01-14:**

| File | Purpose |
|------|---------|
| `schemas/analytics.py` | SearchAnalyticsCreate + PopularQueriesResponse Pydantic schemas |
| `models/analytics.py` | SearchAnalytics SQLAlchemy model |
| `api/v1/analytics.py` | POST and GET endpoints for analytics |
| `migrations/versions/003_create_search_analytics_table.py` | Database migration |

**Endpoints implemented:**
- `POST /api/v1/analytics/search` - Record search query for analytics
- `GET /api/v1/analytics/popular-queries` - Get popular queries with optional days/limit params

### Phase 5: Session Management + Rate Limiting

1. **Implement session middleware**:
   - Generate session_id on first request
   - Store in cookie or return in X-Session-ID header
   - Associate with builds/votes/feedback

2. **Implement rate limiting**:
   - Use slowapi or custom Redis-based limiting
   - Apply limits per endpoint as specified

### Phase 6: Configuration + Database
1. Update `backend/app/config.py`:
   - Remove Milvus/embedding settings
   - Add PostgreSQL connection (platform CNPG)
   - Add Redis/Valkey connection (for cache + rate limiting)
   - Configure CORS for myashes.ai + localhost:8080

2. Create Alembic migration for new tables

### Phase 7: Kubernetes Deployment
1. Create namespace manifest for `myashes-backend`
2. Create Deployment with KEDA ScaledObject
3. Create Service and Ingress
4. Configure Artemis proxy route: `/api/* → myashes-backend:8000`
5. Set up FluxCD Kustomization

### Phase 8: Data Pipeline Migration (Separate Effort)
*This should happen in srt-data-layer repo:*
1. Create `src/connectors/aoc.py` connector
2. Port wiki/codex scraper logic
3. Configure CronJob for daily sync
4. After verified working, delete `data-pipeline/` from this repo

---

## Deployment Requirements (Post-Refactoring)

Once refactoring is complete, deployment must include:

### KEDA Scaling
```yaml
# Example KEDA ScaledObject (to be created)
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: myashes-backend
  namespace: myashes-backend
spec:
  scaleTargetRef:
    name: myashes-backend
  minReplicaCount: 0
  maxReplicaCount: 10
  triggers:
    - type: prometheus
      # TBD: Define scaling metrics
```

### FluxCD Deployment
- Manifests should be in srt-hq-k8s GitOps structure
- Kustomization for environment overlays
- Image automation for Docker Hub updates

### Artemis Integration

Artemis is an NGINX reverse proxy on AWS EC2 that routes public traffic to the K8s cluster.

**Repository**: `/Users/shaun/repos/srt-inference-proxy/`
**Config file**: `nginx.conf` (or `nginx-improved.conf`)

**CORS already configured** for myashes.ai in the `$cors_origin` map:
```nginx
"https://myashes.ai" $http_origin;
"https://www.myashes.ai" $http_origin;
```

**Add upstream definition**:
```nginx
upstream aoc_backend {
    server myashes-backend.myashes-backend.svc.cluster.local:8000;
    keepalive 32;
}
```

**Add location block for `/api/*`**:
```nginx
location /api/ {
    # CORS preflight
    if ($request_method = 'OPTIONS') {
        add_header Access-Control-Allow-Origin $cors_origin always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With, X-Session-ID" always;
        add_header Access-Control-Max-Age 86400 always;
        add_header Content-Length 0;
        add_header Content-Type text/plain;
        return 204;
    }

    # CORS headers
    proxy_hide_header Access-Control-Allow-Origin;
    proxy_hide_header Access-Control-Allow-Methods;
    proxy_hide_header Access-Control-Allow-Headers;
    add_header Access-Control-Allow-Origin $cors_origin always;
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With, X-Session-ID" always;

    proxy_pass http://aoc_backend/api/;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_read_timeout 30s;
    proxy_connect_timeout 5s;
    proxy_send_timeout 30s;

    proxy_intercept_errors on;
    error_page 502 503 504 = @aoc_error;
}

location @aoc_error {
    add_header Content-Type application/json always;
    return 503 '{"error":"MyAshes backend temporarily unavailable","retry_after":5}';
}
```

---

## User Preferences (CRITICAL)

### Shaun's Rules
- ✅ **Complete, working solutions** - Every change must be deployable
- ✅ **No workarounds** - Fix root causes, not symptoms
- ✅ **Git as source of truth** - All changes in code
- ✅ **Documentation first** - Update CLAUDE.md with findings
- ❌ **NO temporary fixes**
- ❌ **NO disabled functionality**

### Agent Behavior
- Run discovery FIRST in any new session
- Update this CLAUDE.md with findings
- Coordinate with myashes.github.io agent on API contracts
- Check srt-data-layer before implementing any data features

---

## Session Workflow

### ~~Discovery~~ COMPLETED 2026-01-14
### ~~Frontend Requirements~~ RECEIVED 2026-01-14
### ~~Phase 1: Cleanup~~ COMPLETED 2026-01-14
### ~~Phase 2: Builds API~~ COMPLETED 2026-01-14
### ~~Phase 3: Feedback API~~ COMPLETED 2026-01-14
### ~~Phase 4: Analytics API~~ COMPLETED 2026-01-14

### Current Work: Phase 7 - Kubernetes Deployment
1. Read this CLAUDE.md
2. **Current Phase**: Phase 7 (K8s deployment to unblock frontend testing)
3. Use `uv` for virtual environment: `cd backend && source .venv/bin/activate`
4. Test locally with: `uv run uvicorn app.main:app --reload`
5. Phase 5 (rate limiting) and Phase 6 (config) can be done after initial deployment

### All Endpoints Implemented ✅
1. ~~**GET /api/v1/builds/{build_id}**~~ ✅ DONE
2. ~~**POST /api/v1/builds**~~ ✅ DONE
3. ~~**GET /api/v1/builds**~~ ✅ DONE
4. ~~**DELETE /api/v1/builds/{build_id}**~~ ✅ DONE
5. ~~**POST /api/v1/builds/{id}/vote**~~ ✅ DONE
6. ~~**POST /api/v1/feedback**~~ ✅ DONE
7. ~~**POST /api/v1/analytics/search**~~ ✅ DONE
8. ~~**GET /api/v1/analytics/popular-queries**~~ ✅ DONE

### When Creating AoC Connector (in srt-data-layer repo)
1. Copy `src/connectors/wikipedia.py` as template
2. Implement `AoCWikiConnector` with Playwright scraping
3. Register in `src/connectors/__init__.py`
4. Add API routes in `src/api/routes/connectors.py`
5. Add to CronJob in `k8s/05-connector-cronjob.yaml`

---

## Change History

| Date | Change | Impact |
|------|--------|--------|
| 2026-01-14 | **PHASE 4 COMPLETE** - All APIs implemented | Builds, Feedback, Analytics - ready for deployment |
| 2026-01-14 | Phase 3 complete - Feedback API | Thumbs up/down on AI responses |
| 2026-01-14 | Phase 2 complete - Builds API | Full CRUD + voting, session middleware, 64-class matrix |
| 2026-01-14 | Phase 1 complete - Deleted redundant code | Removed 15 files, slimmed requirements.txt |
| 2026-01-14 | Plan revised - Integrated frontend requirements | Simplified auth, added new endpoints |
| 2026-01-14 | Frontend requirements received | BACKEND-REQUIREMENTS.md defines exact API contract |
| 2026-01-14 | Discovery complete | Identified redundant code, created initial refactoring plan |
| 2025-12-31 | AI chat LIVE on myashes.ai | Frontend working without this backend |
| 2025-11-12 | Initial K8s manifests | Created but never deployed |

---

## Requirements for srt-data-layer

The following should be added to srt-data-layer:

### New AoC Connector
- **Source**: `src/connectors/aoc.py`
- **Features**:
  - Scrape ashesofcreation.wiki (game data, classes, races, items, etc.)
  - Scrape codex.ashesofcreation.wiki
  - Process official website content
  - Game files extraction (if available)
- **Endpoints**:
  - `POST /v1/connectors/aoc/fetch` - Fetch specific pages
  - `POST /v1/connectors/aoc/sync` - Incremental sync
- **CronJob**: Daily sync at configured time

### Metadata Schema for AoC Content
Documents ingested should include:
- `source`: "aoc-wiki", "aoc-codex", "aoc-official"
- `type`: "class", "race", "item", "skill", "zone", "quest", etc.
- `game_version`: Version/alpha number if applicable
- `category`: Gameplay, World, Items, Systems, etc.

---

**Last Updated**: 2026-01-14
**Status**: Phase 4 COMPLETE - All APIs implemented, ready for deployment
**Next Step**: Phase 7 - Kubernetes deployment to unblock frontend testing

---

*This is a PUBLIC repository for community collaboration. Sensitive platform details are in private repos.*
