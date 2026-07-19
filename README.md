# Lore

### The Artifact Plane for AI Agents.

> Where AI work becomes reusable knowledge.

[![Organization](https://img.shields.io/badge/Org-The--17-blue.svg)](https://github.com/The-17)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Native-green.svg)](https://modelcontextprotocol.io)

> [!WARNING]
> **Work In Progress**: Lore is under active development. APIs are subject to change. Not recommended for production use until a stable release is published.

---

Lore is an open-source workspace where humans and AI agents collaboratively create, version, relate, discover, and reuse **artifacts**.

Instead of scattering work across prompts, local files, and temporary context windows, Lore gives every artifact a persistent identity, complete history, and semantic relationships.

> An artifact is any persistent piece of work or knowledge — documents, code, decisions, skills, conversations, memories, datasets, and more.

---

## The Problem

AI agents create knowledge every day.

Almost none of it survives.

Research gets lost in context windows. Decisions vanish between sessions. Skills are rewritten from scratch. Outputs are dumped into hidden folders where no human ever reviews them.

Lore changes that.

---

## Human Organization + Agent Intelligence

Humans think hierarchically.

```
Projects/
    Client A/
        Research.md
        Proposal.pdf
```

Agents think relationally.

```
Proposal
├── derived from → Research
├── references  → Brand Guidelines
├── created by  → Strategy Agent
├── reviewed by → Human
└── used in     → Sales Campaign
```

Lore supports both simultaneously.

**Collections** give humans familiar folder-based navigation.

**The Artifact Graph** gives agents a queryable map of relationships, dependencies, and provenance.

Neither replaces the other.

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

## What an Artifact Looks Like

```
┌─────────────────────────────────────┐
│  Research: Auth Provider Analysis   │
│                                     │
│  Status        Approved             │
│  Relationships 12                   │
│  Created By    Strategy Agent       │
│  Reviewed By   steppa@the17.co      │
│  Version       5                    │
│  Collection    Projects / Auth      │
└─────────────────────────────────────┘
```

Every artifact has identity, history, relationships, ownership, and lifecycle — whether it was created by a human or an agent.

---

## Build Together

A shared, self-hosted workspace where humans and agents are equal participants.

Immutable version history with line-by-line unified diffs.

Comments, approvals, and lifecycle states.

---

## Build on Previous Work

The Artifact Graph connects every piece of work — research to decisions, decisions to implementations, implementations to deployments.

Semantic search over meaning and relationships, not just filenames.

Full provenance: where it came from, who created it, what depends on it.

---

## Build Efficient Agents

Dynamic skill registry — agents retrieve only the expertise they need, keeping context windows small.

Scoped access tokens restrict agents to specific collections.

Native MCP support for direct integration with Claude, Cursor, Windsurf, and custom agent frameworks.

---

## Built With

- Django + Django Ninja
- PostgreSQL + pgvector
- Model Context Protocol (MCP)

---

## Getting Started

```bash
git clone git@github.com:The-17/Lore.git
cd Lore
pip install -r requirements.txt
make mig
make run
```

Open `http://127.0.0.1:8000/api/docs` to view the interactive API documentation.

See [CONTRIBUTING.md](CONTRIBUTING.md) for full setup and development guidelines.

---

## License

MIT — see [LICENSE](LICENSE).


