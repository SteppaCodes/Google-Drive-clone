# System Architecture: Lore

**Lore** is the **Artifact Plane** — a unified knowledge workspace where humans and AI agents store, version, relate, discover, and collaborate on knowledge.

---

## 1. Technical Stack

* **Backend**: Django 5.x + Django Ninja (high-performance OpenAPI REST layer)
* **Database**: PostgreSQL with `pgvector` indexing (SQLite supported for development)
* **Identity**: `Principal` model unifying `User` (humans) and `AgentToken` (AI agents)
* **Protocol**: Model Context Protocol (MCP) server over stdio and HTTP/SSE JSON-RPC
* **BYOB Architecture**: Bring Your Own Backend support with cross-origin web client integration

---

## 2. Core Concepts

### 2.1 Everything is an Artifact
Instead of flat ephemeral files, outputs have a first-class identity:
* `skill`: Versioned instructions for prompt hydration.
* `decision`: Architecture decisions with rationale and status.
* `memory`: Ephemeral or persistent scratchpad context.
* `document`: Binary or markdown files.

### 2.2 The Artifact Graph & Wiki-Link Parser
* Direct, typed directed edges (`references`, `derived_from`, `depends_on`, `supersedes`, `uses`).
* Automatic parsing of `[[Artifact Title]]` text references creates real-time `references` edges in `ArtifactRelationship`.

### 2.3 Bring Your Own Backend (BYOB)
* Users run their self-hosted Lore backend container on local or cloud infrastructure.
* Dynamic CORS configurations (`LORE_FRONTEND_URL`) permit secure remote web applications to connect to the backend while keeping data 100% self-hosted and private.
