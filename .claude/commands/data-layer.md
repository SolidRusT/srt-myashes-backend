# /data-layer - Spawn Data Layer Agent

Spawn a sub-agent to work in the srt-data-layer repository (shared data platform).

## Repository Details

- **Path**: `/Users/shaun/repos/srt-data-layer/`
- **Purpose**: Shared RAG/vector search platform
- **Tech**: FastAPI, Milvus, Knowledge Graph, LLM orchestration
- **Provides**: `/data/v1/query/*`, `/data/v1/agent/*` endpoints

## Instructions

Use the **Task tool** to spawn a general-purpose sub-agent with:

```
subagent_type: "general-purpose"
prompt: |
  You are working in the srt-data-layer repository at /Users/shaun/repos/srt-data-layer/

  IMPORTANT: First read the CLAUDE.md file at /Users/shaun/repos/srt-data-layer/CLAUDE.md
  to understand the project structure, conventions, and current status.

  Your task: $ARGUMENTS

  After completing the task, provide a summary of:
  - What was done
  - Files modified
  - Any follow-up needed in myashes-backend or frontend
```

Replace `$ARGUMENTS` with the user's request.

## Common Tasks

- Update RAG pipeline
- Modify vector search logic
- Add new data connectors
- Update knowledge graph schema
- Fix embedding/indexing issues

## Context for MyAshes

The data-layer provides these services to MyAshes:
- Semantic search over game content
- AI chat with RAG augmentation
- Knowledge graph queries

## Example Usage

User: "/data-layer Add caching to the semantic search endpoint"

Spawn agent with task to implement caching, noting it affects MyAshes search performance.
