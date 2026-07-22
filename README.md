<div align="center">

# Lore

**The Artifact Plane for Humans and AI Agents.**

[![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Django Ninja](https://img.shields.io/badge/Django_Ninja-FastAPI_for_Django-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://django-ninja.dev)
[![MCP Server](https://img.shields.io/badge/MCP-Protocol_Ready-8A2BE2?style=for-the-badge)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[Quickstart](docs/quickstart.md) • [Tutorial](docs/tutorial.md) • [Architecture](docs/architecture.md) • [Contributing](docs/contributing.md)

</div>

---

## What is Lore?

AI agents are producing more work than teams can manage.
Research, specifications, code, decisions, evaluations, and designs are scattered across chats, repositories, and cloud drives with little history, provenance, or review.

Lore is the Artifact Plane—a system that gives every AI-generated artifact a durable identity, making versioning, collaboration, governance, and reuse possible.
---

## The Problem

Databases manage structured data. Git manages source code. Object stores hold static files. Nothing manages the artifacts an AI agent produces along the way: a piece of research, a draft decision, a generated skill, or a system specification: as governed, ownable, reusable objects.

Because there is no dedicated artifact plane:
* Research gets buried inside an ephemeral context window.
* Architecture decisions made weeks ago must be re-derived because outputs were discarded.
* Generated code or draft proposals pile up in hidden folders no human ever reviews.
* System prompts balloon with static instructions because agents cannot dynamically fetch skill artifacts.

---

## How It Fits Together

```
                Human
                  │
                  ▼
            ┌────────────┐
            │    Lore    │
            │  Artifact  │
            │   Plane    │
            └─────┬──────┘
                  │
         ┌────────┴────────┐
         ▼                 ▼
   Collections       Artifact Graph
   (navigation)      (relationships)
                  ▲
                  │
              AI Agents
```

## Human Organization + Agent Intelligence

Humans think hierarchically:

```
Projects/
    Client A/
        Research.md
        Proposal.pdf
```

Agents think relationally:

```
Proposal
├── derived_from → Research
├── references   → Brand Guidelines
├── created_by   → Strategy Agent
├── reviewed_by  → Human Admin
└── used_in      → Sales Campaign
```

Lore supports both at once:
* **Collections** give humans familiar folder-based navigation and database-backed permission inheritance.
* **The Artifact Graph** gives agents a queryable map of dependencies and provenance.

Neither replaces the other. Both operate on the same underlying artifact.

---

## Core Capabilities

### Bring Your Own Backend (BYOB)
Lore is built for self-hosting. Keep 100% of your data on your own infrastructure. Lore backends run via Docker or Python environments, providing configurable CORS settings (`LORE_FRONTEND_URL`) so static web applications can connect securely to your private API.

### Model Context Protocol (MCP) Server
Native JSON-RPC server running over **stdio** (`python manage.py mcp_server`) and **HTTP/SSE** (`/api/mcp/`). Connect Claude Desktop, Cursor, Windsurf, or custom agent frameworks using 7 core tools:
* `search_artifacts`: Search artifacts by query string across accessible collections.
* `read_artifact`: Retrieve full metadata, version number, and content.
* `write_artifact`: Create or update artifacts with automatic version diffs and wiki-link extraction.
* `revert_artifact`: Revert an artifact to a previous version snapshot in an append-only audit trail.
* `list_collection`: List sub-collections and artifacts inside a scope.
* `create_relationship`: Create typed graph edges between artifacts.
* `list_skills`: List registered skill artifacts accessible to the caller.

### Dynamic Skill Registry
Agents fetch versioned instructions on-demand via `/api/artifacts/skills/{title}` rather than cluttering system prompts. Tracks skill `usage_count` automatically on read.

### Automatic Wiki-Link Graph Relations
Text content containing `[[Artifact Title]]` syntax automatically parses matching workspace artifacts on save and creates directed `references` relationship edges in the Artifact Graph.

### Optimistic Concurrency Control & Version Rollbacks
* **OCC Conflict Guard**: Detects concurrent edits between swarm agents via `expected_version_number` (`409 Conflict`).
* **Append-Only Rollbacks**: Revert an artifact to any historical version snapshot without destroying audit history (`POST /api/artifacts/{id}/revert`).

### Incremental Vector & Text RAG Chunking
Sliding-window text chunker (`ArtifactChunk`) indexes version snapshots automatically, providing granular RAG snippet search (`/api/artifacts/chunks/search`).

---

## A Day in Lore

```
Agent produces a piece of research.
       │
       ▼
Saves it as a Research Artifact inside a Collection.
       │
       ▼
Links it to three prior Architecture Decision artifacts via [[Wiki-Links]].
       │
       ▼
Human reviews the line-by-line diff, leaves a comment, and Approves.
       │
       ▼
Another agent discovers the approved artifact weeks later
and builds directly on top of it.
```

---

## What an Artifact Looks Like

```
┌──────────────────────────────────────────┐
│  Research: Auth Provider Analysis        │
│                                          │
│  Status        Approved                  │
│  Relationships 12 Graph Edges            │
│  Created By    Strategy Agent (Principal) │
│  Reviewed By   admin@lore.com (Principal) │
│  Version       v5 (Line Diffs Recorded)   │
│  Collection    Projects / Auth           │
└──────────────────────────────────────────┘
```

---

## Quickstart (Local Development)

```bash
# 1. Clone the repository
git clone https://github.com/The-17/Lore.git
cd Lore

# 2. Set up virtual environment
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# 3. Migrate database & start server
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Open Swagger UI documentation at `http://127.0.0.1:8000/api/docs`.

For detailed setup instructions, read the **[Quickstart Guide](docs/quickstart.md)**.

---

## Connecting Claude Desktop (MCP Stdio)

Issue an agent token and add Lore to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lore": {
      "command": "/path/to/Lore/env/bin/python3",
      "args": ["manage.py", "mcp_server", "--token", "lore_agent_YOUR_TOKEN"],
      "cwd": "/path/to/Lore"
    }
  }
}
```

---

## Documentation

* **[Quickstart Guide](docs/quickstart.md)**: Local installation, environment configuration, and MCP setup.
* **[Step-by-Step Tutorial](docs/tutorial.md)**: Working with collections, wiki-links, version diffs, and skill registry.
* **[System Architecture](docs/architecture.md)**: Technical design, `Principal` identity model, and BYOB specs.
* **[Contributor Guide](docs/contributing.md)**: Development setup, coding guidelines, and PR workflow.

---

## Built With

* Django + Django Ninja
* PostgreSQL + pgvector (SQLite supported for development)
* Model Context Protocol (MCP)

---

## License

Lore is open-source software licensed under the **[MIT License](LICENSE)**.
