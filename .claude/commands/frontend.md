# /frontend - Spawn Frontend Agent

Spawn a sub-agent to work in the MyAshes frontend repository (myashes.github.io).

## Repository Details

- **Path**: `/Users/shaun/repos/myashes.github.io/`
- **Purpose**: Static frontend for myashes.ai (GitHub Pages)
- **Tech**: Vanilla JS, ES6 modules, localStorage for state
- **Live URL**: https://myashes.ai

## Instructions

Use the **Task tool** to spawn a general-purpose sub-agent with:

```
subagent_type: "general-purpose"
prompt: |
  You are working in the MyAshes frontend repository at /Users/shaun/repos/myashes.github.io/

  IMPORTANT: First read the CLAUDE.md file at /Users/shaun/repos/myashes.github.io/CLAUDE.md
  to understand the project structure, conventions, and current status.

  Your task: $ARGUMENTS

  After completing the task, provide a summary of:
  - What was done
  - Files modified
  - Any follow-up needed in the backend or other repos
```

Replace `$ARGUMENTS` with the user's request.

## Common Tasks

- Update UI components
- Fix frontend bugs
- Add new features to the chat interface
- Update build sharing UI
- Modify API integration code

## Context Sharing

When spawning the agent, include relevant context from this backend session:
- API endpoint changes
- New features deployed
- Schema changes that affect frontend

## Example Usage

User: "/frontend Add a loading spinner to the build list"

Spawn agent with task to implement loading spinner, referencing the builds API endpoint.
