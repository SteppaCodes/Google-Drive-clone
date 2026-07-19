# Lore

**The Artifact Plane.**

Where human and AI work becomes reusable, reviewable, and permanent.

`Organization` `License: MIT` `MCP`

> **Work In Progress**: Lore is under active development. APIs are subject to change. Not recommended for production use until a stable release is published.

Lore is a workspace where humans and AI agents create, version, relate, and build on top of **artifacts** — persistent units of work with identity, history, and provenance.

Artifacts aren't memories. Memory systems capture facts an agent should remember. Lore captures the work an agent produces — documents, code, decisions, skills, datasets — with identity, history, review, and provenance.

## The Problem

Software has databases for data. Git repositories for code. Object stores for files. AI systems need an Artifact Plane: a place where the work they produce becomes durable, reviewable, and reusable.

Right now, that place doesn't exist. AI agents produce artifacts every day (research, drafts, decisions, code) and almost none of it becomes reusable.

Work gets lost in context windows. Decisions vanish between sessions. Drafts are rewritten from scratch because no one can find the last version. Output gets dumped into folders no human ever reviews.

Lore gives every artifact an identity that outlives the session that created it.

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
├── derived from → Research
├── references  → Brand Guidelines
├── created by  → Strategy Agent
├── reviewed by → Human
└── used in     → Sales Campaign
```

Lore supports both at once.

**Collections** give humans familiar folder-based navigation.
**The Artifact Graph** gives agents a queryable map of dependencies and provenance.

Neither replaces the other.

## A Day in Lore

```
Agent produces a piece of work.
       │
       ▼
Saves it as a Research Artifact inside a Collection.
       │
       ▼
Links it to three prior Architecture Decision artifacts.
       │
       ▼
Human reviews the unified diff, leaves a comment, and Approves.
       │
       ▼
Another agent discovers the approved artifact six weeks later
and builds directly on top of it.
```

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

Every artifact has identity, history, relationships, ownership, and lifecycle — whether a human or an agent created it.

## Build Together

A shared, self-hosted workspace where humans and agents are equal participants in producing work, not just consuming it.

Lore applies ideas like version control, editorial review, and provenance to AI-generated work.

- Immutable version history with line-by-line unified diffs
- Comments, approvals, and lifecycle states
- Full authorship trail for every artifact, human or agent

## Build on Previous Work

The Artifact Graph connects every piece of work an agent or human has produced — research to decisions, decisions to implementations, implementations to deployments.

- Semantic search over artifacts and their relationships, not just filenames
- Full provenance: where an artifact came from, who touched it, what depends on it

## Build Efficient Agents

- **Skill artifact store** — skills live in Lore like any other artifact. Lore doesn't select or route skills; agents pull only the ones they need, keeping context windows small.
- **Scoped access tokens** restrict agents to specific collections.
- **Native MCP support** for direct integration with Claude, Cursor, Windsurf, and custom agent frameworks.

## Built With

- Django + Django Ninja
- PostgreSQL + pgvector
- Model Context Protocol (MCP)

## Getting Started

```bash
git clone git@github.com:The-17/Lore.git
cd Lore
pip install -r requirements.txt
make mig
make run
```

Open `http://127.0.0.1:8000/api/docs` to view the interactive API documentation.

See `CONTRIBUTING.md` for full setup and development guidelines.

## License

MIT — see `LICENSE`.
