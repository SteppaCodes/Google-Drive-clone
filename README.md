# Lore

**The Artifact Plane.**


> **Work In Progress**: Lore is under active development. APIs are subject to change. Not recommended for production use until a stable release is published.

An Artifact Plane is the infrastructure layer responsible for storing, governing, relating, and serving the artifacts produced by intelligent systems.

AI agents don't just generate text. They produce artifacts — research reports, source code, decisions, specifications, skills, evaluations, datasets.

Existing systems primarily treat AI-generated artifacts as files. Lore treats them as first-class objects with identity, history, relationships, review, and governance — built for artifact management, not general-purpose storage.

**Lore gives every artifact a stable identity.** That identity is what makes versioning, provenance, relationships, review, ownership, and governance possible.

## Who It's For

Lore is built for teams building AI agents, multi-agent systems, and AI-powered products that need durable, governed artifacts instead of disposable outputs — agent platform builders, AI engineering teams, and research teams who need their agents' work to survive past a single session.

## The Problem

Databases manage data. Git manages source code. Object stores hold files. Nothing manages the artifacts an AI agent produces along the way — a piece of research, a draft decision, a generated skill, a design — as governed, ownable, reusable objects.

So they get lost. Research gets buried in a context window. A decision made six weeks ago has to be re-derived because no one can find it. A draft gets rewritten from scratch because the last version is gone. Output piles up in a folder no human ever reviews.

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
├── derived from → Research
├── references  → Brand Guidelines
├── created by  → Strategy Agent
├── reviewed by → Human
└── used in     → Sales Campaign
```

Lore supports both at once.

**Collections** give humans familiar folder-based navigation.
**The Artifact Graph** gives agents a queryable map of dependencies and provenance.

Neither replaces the other — both are in service of the same artifact.

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

A shared, self-hosted workspace where humans and agents are equal participants in producing and governing work, not just consuming it.

- Immutable version history with line-by-line unified diffs
- Comments, approvals, and lifecycle states
- Full authorship trail for every artifact, human or agent

## Build on Previous Work

The Artifact Graph connects every artifact a human or agent has produced — research to decisions, decisions to implementations, implementations to deployments.

- Semantic search over artifacts and their relationships, not just filenames
- Full provenance: where an artifact came from, who touched it, what depends on it

## Build Efficient Agents

- **Skill artifact store** — skills are artifacts like any other. Lore doesn't select or route them; agents pull only the ones they need, keeping context windows small.
- **Scoped access tokens** restrict agents to specific collections.
- **Native MCP support** for direct integration with Claude, Cursor, Windsurf, and custom agent frameworks.

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

## Built With

- Django + Django Ninja
- PostgreSQL + pgvector
- Model Context Protocol (MCP)

## License

MIT — see `LICENSE`.
