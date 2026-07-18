# Lore

### Self-Hosted, Collaborative Memory & Artifact Vault for AI Agents and Humans

[![Organization](https://img.shields.io/badge/Org-The--17-blue.svg)](https://github.com/The-17)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Native-green.svg)](https://modelcontextprotocol.io)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20pgvector-blue.svg)](https://github.com/pgvector/pgvector)

**Lore** is an open-source, self-hosted workspace and knowledge vault built from the ground up for hybrid collaboration between **AI Agents** and **Humans**. It combines the permission-aware folder structures of Google Drive, the bidirectional markdown note-graphing of Obsidian, and the native tool-connectivity of the Model Context Protocol (MCP) into a single, light, and semantic-search-enabled database.

---

## The Problem: The Agent Memory Crisis

As LLMs transition from chatbots to autonomous software agents, they encounter a critical bottleneck in how they access, store, and share knowledge:

1. **The RAG Context Drawer**: Dumping raw files or transcripts into vector databases yields irrelevant, bloated context chunks. Agents lose reasoning ability and run up massive API costs trying to parse noise.
2. **The Amnesia Trap**: Agents lack persistent, cumulative state. A decision or lesson learned on Project A cannot be accessed by an agent working on Project B. Every run starts cold.
3. **The Artifact Black Hole**: Coding and research agents dump intermediate drafts, logs, schemas, and configurations into hidden local folders or ephemeral Docker containers. Humans have zero visibility, no review interface, and no control over what the agent writes.
4. **The Blackboard Coordination Gap**: Multi-agent loops lack a secure, shared blackboard. Agents writing to the same filesystem encounter race conditions, file corruption, or permission violations.

---

## The Solution: Lore

Lore is the dedicated **memory, skill, and artifact plane** for human-agent collaboration. It decouples the agent's reasoning guidelines and decision history from the target code repository, offering:

*   **A Shared Workspace**: A secure, self-hosted web vault where humans and agents co-exist as first-class users.
*   **Version Control & Diffs**: Every agent file write automatically generates a new version with line-by-line unified diffs, giving humans a visual review layer to audit or revert agent changes.
*   **Dynamic Skill Store**: Agents load only the specific `SKILL.md` they need for a task via the MCP tool registry, reducing context window sizes by up to 60%.
*   **Global Precedent Sync**: A centralized `decision-log.md` compiles lessons across the network. When one agent learns a rule, all other agents inherit it instantly.

---

## Core Paradigm

```
  Human User  ──► [ Web Dashboard & Graph UI ] ◄──  AI Agent
                            │
                            ▼
             [ Lore Django Ninja API Server ]
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
   [ pgvector RAG ]                   [ Version Diff Control ]
   (Semantic Chunks)                  (difflib tracking)
```

1. **Context Efficiency (Dynamic Skills)**: Instead of loading massive prompts, agents query Lore's `/skills/` registry dynamically via MCP, loading only what they need for a task.
2. **Global Agent Memory**: Decision logs (`decision-log.md`) are synced across all projects on the network. When one agent learns, all other agents learn.
3. **Out-of-Repo Audits**: Agents write execution drafts (`harness_audit.md`) directly to Lore under `/audits/` for human review, keeping the target codebase clean.

---

## Key Features

- **Model Context Protocol (MCP)**: Native stdio and HTTP/SSE JSON-RPC tools (`read_document`, `write_document`, `search_documents`, `list_directory`). Supports immediate mounting inside Cursor, Claude Desktop, Windsurf, or custom LangChain setups.
- **Sandboxed Scope Tokens**: Generate revocable API tokens for agents scoped to specific folders. Agents are blocked from accessing files outside their boundary.
- **Version Control & Diffs**: Every agent write generates a new version. The Web UI renders color-coded unified diffs (additions/deletions) for quick human auditing and rollbacks.
- **Obsidian-Style Links**: Extracts bidirectional wiki-links (`[[target-note]]`) automatically on file saves to map out a relational visualization of agent knowledge.
- **Semantic Search**: Text/markdown uploads are chunked and embedded in PostgreSQL using `pgvector` to return context-rich semantic passages, not giant raw files.

---

## Architecture

```
                               ┌───────────────┐
                               │  Human User   │
                               └───────┬───────┘
                                       │ Web UI & Graph view
                                       ▼
┌───────────────┐  MCP tools   ┌───────────────┐
│   AI Agent    ├─────────────►│  Lore Server  │
└───────────────┘  (JSON-RPC)  └───────┬───────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
  [ PostgreSQL + pgvector ]     [ Local / S3 Storage ]       [ Worker Queue ]
  - Metadata & Embeddings       - Versioned raw files        - Chunking & embeddings
  - Bidirectional links         - Diff history               - Link parser hook
```

---

## Installation Guide

### Prerequisites
- Python 3.10+
- PostgreSQL with the `pgvector` extension

### Quick Setup

1.  **Clone and Navigate**
    ```bash
    git clone git@github.com:The-17/Lore.git
    cd Lore
    ```

2.  **Create and Activate Virtual Environment**
    ```bash
    python -m venv env
    source env/bin/activate  # Windows: env\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    pip install django-ninja
    ```

4.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```env
    SETTINGS=base
    SECRET_KEY=your-django-secret-key
    DB_ENGINE=django.db.backends.sqlite3
    ```

5.  **Run Migrations & Start Development Server**
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```
    Open your browser to `http://127.0.0.1:8000/api/docs` to view the interactive Swagger API documentation.

---

## Connecting Your Agent via MCP

To mount Lore as a tool inside **Claude Desktop**, add the server to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lore": {
      "command": "python",
      "args": ["/path/to/Lore/manage.py", "run_mcp_server"],
      "env": {
        "LORE_API_TOKEN": "lore_agent_access_token_yourhash"
      }
    }
  }
}
```

---

## Directory Layout

```
Lore/
├── apps/
│   ├── accounts/     # Identity, Permissions, and Scoped Agent Tokens
│   ├── common/       # Middleware, Ninja Auth, & Base Models
│   ├── files/        # File Ingestion, Version Control, & Comments
│   ├── folders/      # Scoped folder structures
│   └── __init__.py
├── lore/
│   ├── settings/     # Configuration suite
│   ├── api.py        # Central Django Ninja entrypoint
│   ├── urls.py       # Global endpoint routing
│   ├── wsgi.py
│   └── asgi.py
├── manage.py
└── requirements.txt
```

---

## Contributing

We welcome contributions from the developer community. Please read our [Contributing Guidelines](CONTRIBUTING.md) to get started.

---

## License

Lore is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
