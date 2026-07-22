<div align="center">

# Lore — The Artifact Plane for AI Agents & Humans

**Where AI agent outputs become reusable, versioned, relational knowledge.**

[![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Django Ninja](https://img.shields.io/badge/Django_Ninja-FastAPI_for_Django-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://django-ninja.dev)
[![MCP Server](https://img.shields.io/badge/MCP-Protocol_Ready-8A2BE2?style=for-the-badge)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[Quickstart](docs/quickstart.md) • [Tutorial](docs/tutorial.md) • [Architecture](docs/architecture.md) • [Contributing](docs/contributing.md)

</div>

---

## 💡 What is Lore?

AI agents create knowledge every day — research, decisions, skills, code, plans — but almost none of it survives:
1. **Amnesia & Context Bloat**: Agents reload massive static system prompts for every session, burning tokens and forgetting past decisions.
2. **Scatter & Isolation**: Agent outputs are dumped into hidden scratchpads, temporary docker volumes, or buried in prompt logs where no human ever reviews them.
3. **Flat Filesystem Mismatch**: Filesystems group work by rigid hierarchy, whereas agents think relationally (tracing how a decision authorized a proposal derived from research).

**Lore is the Artifact Plane** where humans and AI agents store, version, relate, discover, and collaborate on knowledge.

---

## ✨ Key Features

### 🏢 Bring Your Own Backend (BYOB)
Keep 100% of your data on your own infrastructure. Lore backends are self-hostable via Docker, offering flexible CORS controls (`LORE_FRONTEND_URL`) so web applications can connect securely to your private API.

### 🤖 Model Context Protocol (MCP) Server
Native JSON-RPC server over both **stdio** (`python manage.py mcp_server`) and **HTTP/SSE** (`/api/mcp/`). Connect Claude Desktop, Cursor, Windsurf, or custom AI agents in under 60 seconds with 7 pre-built tools:
* `search_artifacts` • `read_artifact` • `write_artifact` • `revert_artifact` • `list_collection` • `create_relationship` • `list_skills`

### ⚡ Dynamic Skill Registry
Agents fetch versioned instructions on-demand via `/api/artifacts/skills/{title}` rather than cluttering system prompts. Tracks skill `usage_count` automatically.

### 🕸️ The Artifact Graph & Wiki-Link Auto-Extraction
Text containing `[[Artifact Title]]` syntax automatically parses matching workspace artifacts on save and creates queryable `references` relationship edges.

### 🛡️ Optimistic Concurrency Control (OCC) & Append-Only Rollbacks
* **OCC**: Detects concurrent edits between swarm agents via `expected_version_number` (`409 Conflict`).
* **Rollbacks**: Revert an artifact to any historical version snapshot without destroying audit history (`POST /api/artifacts/{id}/revert`).

### 🔍 Incremental Vector & Text RAG Chunking
Sliding-window text chunker (`ArtifactChunk`) indexes version snapshots automatically, providing granular RAG snippet search (`/api/artifacts/chunks/search`).

---

## ⚡ Quickstart (Local Development)

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

Open Swagger UI documentation at **`http://127.0.0.1:8000/api/docs`**.

For detailed setup instructions, read the **[Quickstart Guide](docs/quickstart.md)**.

---

## 🔌 Connecting Claude Desktop (MCP Stdio)

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

## 📚 Documentation

* 🚀 **[Quickstart Guide](docs/quickstart.md)**: Local installation, environment configuration, and MCP setup.
* 📖 **[Step-by-Step Tutorial](docs/tutorial.md)**: Working with collections, wiki-links, version diffs, and skill registry.
* 🏛️ **[System Architecture](docs/architecture.md)**: Technical design, `Principal` identity model, and BYOB specs.
* 🤝 **[Contributor Guide](docs/contributing.md)**: Development setup, coding guidelines, and PR workflow.

---

## 📄 License

Lore is open-source software licensed under the **[MIT License](LICENSE)**.
