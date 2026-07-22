# Lore Quickstart Guide

Get up and running with **Lore** — the Artifact Plane for Humans and AI Agents.

---

## 1. Prerequisites

* **Python**: 3.12 or higher
* **Database**: PostgreSQL (recommended for production) or SQLite (for local testing)
* **Package Manager**: `venv` + `pip`

---

## 2. Local Setup & Installation

### Step 1: Clone the repository
```bash
git clone https://github.com/The-17/Lore.git
cd Lore
```

### Step 2: Create virtual environment & install dependencies
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Key configuration settings:
```ini
SECRET_KEY=your-secure-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
LORE_FRONTEND_URL=http://localhost:5173,https://app.lore.dev
```

### Step 4: Run Database Migrations
```bash
python manage.py migrate
```

### Step 5: Start the Development Server
```bash
python manage.py runserver
```
* **API Base URL**: `http://127.0.0.1:8000/api`
* **Swagger UI Documentation**: `http://127.0.0.1:8000/api/docs`

---

## 3. First-Time Admin Registration

Register the initial workspace admin account:
```bash
curl -s -X POST "http://127.0.0.1:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@lore.com",
    "password": "supersecret123",
    "first_name": "Admin",
    "last_name": "User"
  }'
```

Save your `access_token` from the response to authenticate future API calls.

---

## 4. Connecting AI Agents via Model Context Protocol (MCP)

Lore supports native **MCP integration** over stdio and HTTP/SSE.

### Option A: Stdio MCP Server (Claude Desktop / Cursor CLI)
Issue an agent token first:
```bash
curl -s -X POST "http://127.0.0.1:8000/api/auth/tokens" \
  -H "Authorization: Bearer <YOUR_ADMIN_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"description": "Claude Desktop", "scope": "read_write"}'
```

Add Lore to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "lore": {
      "command": "/path/to/Lore/env/bin/python3",
      "args": ["manage.py", "mcp_server", "--token", "lore_agent_<YOUR_AGENT_TOKEN>"],
      "cwd": "/path/to/Lore"
    }
  }
}
```

### Option B: HTTP/SSE MCP Endpoint
Connect any HTTP-compatible agent directly to:
```
POST http://127.0.0.1:8000/api/mcp/
Authorization: Bearer lore_agent_<YOUR_AGENT_TOKEN>
```
