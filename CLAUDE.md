# CLAUDE.md - Ashes of Creation Assistant Backend

**Project**: Community backend for Ashes of Creation game assistant
**Status**: NEEDS DISCOVERY & REFACTORING - Built before shared platform existed
**Visibility**: PUBLIC (community collaboration)
**Last Updated**: 2026-01-14
**Shaun's Golden Rule**: **No workarounds, no temporary fixes, no disabled functionality. Full solutions only.**

---

## CRITICAL: READ THIS FIRST

This repository was built **before** the SolidRusT shared platform matured. The platform now provides:
- **srt-data-layer**: RAG, vector search, MeiliSearch, Milvus, knowledge graph
- **srt-hq-k8s**: Mature K8s cluster with KEDA, FluxCD, Artemis proxy
- **Artemis**: Inference proxy with CORS for frontend integration

**Your first task in any session**: Run discovery to understand what this repo does and what's redundant.

---

## Strategic Context

```
┌─────────────────────────────────────────────────────────────┐
│  myashes.github.io (PRIVATE)                                │
│  - Frontend at https://myashes.ai                           │
│  - Flagship product for SolidRusT Networks                  │
│  - Already LIVE with AI chat via Artemis                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Artemis Proxy (AWS)                                        │
│  - CORS-enabled gateway for all API calls                   │
│  - Routes to K8s services                                   │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────────┐
│  srt-data-layer       │       │  THIS REPO (when deployed)│
│  - RAG/vector search  │       │  - User accounts?         │
│  - MeiliSearch        │       │  - Build sharing?         │
│  - Milvus embeddings  │       │  - Discord bot?           │
│  - Knowledge graph    │       │  - What else is needed?   │
│  ✅ ALREADY DEPLOYED  │       │  ⚠️ NOT YET DEPLOYED      │
└───────────────────────┘       └───────────────────────────┘
```

---

## Discovery Checklist

Before any implementation work, you MUST understand:

### 1. What does this repo currently provide?
- [ ] Review `backend/app/api/v1/` - what endpoints exist?
- [ ] Review `backend/app/services/` - what services are implemented?
- [ ] Review `backend/app/models/` - what database models exist?
- [ ] Review `data-pipeline/` - what scraping/ingestion exists?

### 2. What's now handled by srt-data-layer?
- [ ] Check `/Users/shaun/repos/srt-data-layer/CLAUDE.md`
- [ ] Vector search / embeddings → likely redundant
- [ ] RAG / semantic search → likely redundant
- [ ] Knowledge base queries → likely redundant

### 3. What's still needed from this repo?
- [ ] User authentication (JWT)?
- [ ] User accounts and profiles?
- [ ] Character build persistence?
- [ ] Build sharing / social features?
- [ ] Discord bot integration?
- [ ] Rate limiting / usage tracking?

### 4. What should move TO srt-data-layer?
- [ ] Any data ingestion pipelines?
- [ ] Any scraper configurations?
- [ ] Any embedding logic?

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

---

## Related Repositories

| Resource | Location | Purpose |
|----------|----------|---------|
| **Frontend** | `/Users/shaun/repos/myashes.github.io/` | Live at myashes.ai |
| **Data Layer** | `/Users/shaun/repos/srt-data-layer/` | RAG/vector platform |
| **K8s Platform** | `/Users/shaun/repos/srt-hq-k8s/` | Infrastructure |
| **Artemis** | `/Users/shaun/repos/srt-inference-proxy/` | API gateway |

---

## Project Structure

```
ashes-of-creation-assistant/
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API endpoints (REVIEW FOR REDUNDANCY)
│   │   ├── services/          # Business logic (REVIEW FOR REDUNDANCY)
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── crud/              # Database operations
│   │   └── main.py            # Application entry point
│   ├── migrations/            # Alembic migrations
│   └── requirements.txt       # Dependencies
├── frontend/                  # Next.js (NOT USED - myashes.github.io instead)
├── data-pipeline/             # Scrapers (REVIEW - may move to srt-data-layer)
├── k8s/                       # K8s manifests (NEEDS KEDA + FluxCD update)
├── Dockerfile
└── CLAUDE.md                  # This file
```

---

## Current State Assessment (NEEDS UPDATE)

After discovery, update this section with findings:

### Services in this repo:
| Service | Purpose | Status | Action |
|---------|---------|--------|--------|
| TBD | TBD | TBD | TBD |

### Redundant with srt-data-layer:
| Feature | This Repo | srt-data-layer | Decision |
|---------|-----------|----------------|----------|
| TBD | TBD | TBD | TBD |

### Still Needed:
| Feature | Priority | Notes |
|---------|----------|-------|
| TBD | TBD | TBD |

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
- Register endpoints with Artemis proxy
- Configure CORS for myashes.ai
- Set up health checks

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

### First Session (Discovery)
1. Read this entire CLAUDE.md
2. Explore `backend/app/` to understand what exists
3. Compare with srt-data-layer capabilities
4. Update "Current State Assessment" section above
5. Identify redundant vs needed services
6. Propose refactoring plan

### Subsequent Sessions
1. Read this CLAUDE.md (will have discovery findings)
2. Continue refactoring based on plan
3. Update manifests for KEDA + FluxCD
4. Test integration with srt-data-layer
5. Coordinate API contracts with frontend agent

---

## Change History

| Date | Change | Impact |
|------|--------|--------|
| 2026-01-14 | CLAUDE.md rewritten for discovery | Agent now understands platform integration needs |
| 2025-12-31 | AI chat LIVE on myashes.ai | Frontend working without this backend |
| 2025-11-12 | Initial K8s manifests | Created but never deployed |

---

**Last Updated**: 2026-01-14
**Status**: NEEDS DISCOVERY & REFACTORING
**Next Step**: Run discovery, update this file with findings

---

*This is a PUBLIC repository for community collaboration. Sensitive platform details are in private repos.*
