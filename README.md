# Lore

## Where AI work becomes reusable knowledge.

[![Organization](https://img.shields.io/badge/Org-The--17-blue.svg)](https://github.com/The-17)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Native-green.svg)](https://modelcontextprotocol.io)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20pgvector-blue.svg)](https://github.com/pgvector/pgvector)

> [!WARNING]
> **Work In Progress (WIP)**: Lore is under active development. The codebase is experimental and APIs are subject to change. Until a stable release tag is published, it is not recommended for production use.

---

## The Vision: The Artifact Plane

AI agents create knowledge every day—but almost none of it becomes reusable. Today's agents operate in isolated context windows or temporary local scratchpads. When they research, make decisions, or write code, they suffer from amnesia. They scatter outputs across filesystems, lose history, and repeatedly reload massive prompts instead of building on a persistent, shared memory.

**Lore is the Artifact Plane** where humans and AI agents store, relate, version, discover, and collaborate on knowledge. 

Humans experience Lore as a familiar, hierarchical collaborative workspace (like Google Drive). AI agents experience Lore as a rich, queryable knowledge graph. Both interact with the same underlying model where everything—documents, code, decisions, memories, and skills—is a first-class **Artifact**.

---

## Human Organization + Agent Intelligence

Lore bridges how humans and agents naturally process information:

*   **Humans think hierarchically**: We organize work in nested folders (**Collections**) for intuitive navigation and permission management.
*   **Agents think relationally**: They query connections (**The Artifact Graph**)—tracing how an implementation plan was derived from a research document, what decision authorized it, and which agent executed it.

Neither model replaces the other. Lore supports both simultaneously.

---

## What Lore Gives You

*   **Shared Workspace**: A secure, self-hosted workspace where humans and agents build knowledge together.
*   **Immutable Version History**: Every agent write automatically records a new version with line-by-line unified diffs. Humans audit, approve, or revert agent edits in a visual review interface.
*   **The Artifact Graph**: Bidirectional linking that builds a queryable semantic map of the entire workspace. Agents trace relationships, dependencies, and provenance.
*   **Dynamic Skill Registry**: Instead of wasting context windows on massive system prompts, agents retrieve specific, versioned skill files dynamically.
*   **Sandboxed Scoping**: Provision scoped access tokens that restrict agents to specific collections. They are sandboxed from reading or writing outside their boundary.
*   **Semantic Search**: High-performance semantic search operating over chunks of text, allowing humans and agents to search by meaning and relationship rather than just filenames.

---

## A Day in Lore

```
Agent researches a task.
       │
       ▼
Creates a Research Artifact inside a Collection.
       │
       ▼
Links the draft to three previous Architecture Decisions.
       │
       ▼
Human reviews the unified diff, leaves a comment, and Approves.
       │
       ▼
Another agent discovers the approved knowledge six weeks later.
```

---

## Technical Architecture

Lore is designed as a lean backend service providing REST and MCP APIs:

*   **Core Services**: Built on Django with high-performance Postgres + `pgvector` for semantic indexing.
*   **Unified Identity**: A single `Principal` registry handles human users, agent tokens, and system actions uniformly.
*   **Model Context Protocol (MCP)**: Native stdio and HTTP/SSE JSON-RPC endpoints that expose tools directly to LLM clients.

---

## Getting Started

Detailed instructions for setup and contribution are maintained in:
- [CONTRIBUTING.md](CONTRIBUTING.md) — Developer setup, style guidelines, and running tests.
- [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md) — Step-by-step verification flows.

### Quick Install

1. **Clone the repository**
   ```bash
   git clone git@github.com:The-17/Lore.git
   cd Lore
   ```

2. **Configure environment**
   Create a `.env` file in the root directory:
   ```env
   SETTINGS=base
   SECRET_KEY=your-django-secret-key
   DB_ENGINE=django.db.backends.sqlite3
   ```

3. **Install & run**
   ```bash
   pip install -r requirements.txt
   make mig
   make run
   ```
   Open your browser to `http://127.0.0.1:8000/api/docs` to view the interactive API documentation.

---

## License

Lore is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

