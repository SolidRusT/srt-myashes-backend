# MyAshes.ai Backend

Backend API for [MyAshes.ai](https://myashes.ai) - an AI-powered assistant for Ashes of Creation.

## What This Repo Provides

Product-specific backend services for the MyAshes.ai community platform:

- **Build Sharing** - Create, share, and vote on character builds
- **Feedback Collection** - Thumbs up/down on AI responses
- **Search Analytics** - Track popular queries and search patterns

## Architecture

```
myashes.ai (GitHub Pages)
    │
    ▼
Artemis Proxy (artemis.hq.solidrust.net)
    │
    ├── /data/* → srt-data-layer (AI chat, vector search)
    └── /api/*  → THIS BACKEND (builds, feedback, analytics)
```

The AI chat functionality is provided by [srt-data-layer](https://github.com/SolidRusT/srt-data-layer),
a shared platform service. This repo only handles the MyAshes-specific features.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET/POST /api/v1/builds` | List and create builds |
| `GET/PATCH/DELETE /api/v1/builds/{id}` | Get, update, delete build |
| `POST /api/v1/builds/{id}/vote` | Vote on a build (1-5) |
| `POST /api/v1/feedback` | Submit AI response feedback |
| `POST /api/v1/analytics/search` | Record search query |
| `GET /api/v1/analytics/popular-queries` | Get trending queries |

## Deployment

This backend runs on Kubernetes with:
- 6 replicas auto-scaled via KEDA
- PostgreSQL for persistence
- Valkey for caching
- Prometheus metrics at `/metrics`

See [CLAUDE.md](CLAUDE.md) for detailed technical documentation.

## Development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Related Repos

| Repo | Purpose |
|------|---------|
| [myashes.github.io](https://github.com/myashes/myashes.github.io) | Frontend (live at myashes.ai) |
| [srt-data-layer](https://github.com/SolidRusT/srt-data-layer) | AI/RAG platform |
| [srt-hq-k8s](https://github.com/SolidRusT/srt-hq-k8s) | K8s infrastructure |

## License

MIT License. Ashes of Creation is a trademark of Intrepid Studios. This is a fan project.
