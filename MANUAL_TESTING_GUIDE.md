# Manual Testing Guide: Lore Memory Plane

This guide provides step-by-step instructions to manually test the entire Lore collaborative memory plane locally. It covers human user authentication, folder hierarchical operations, file upload/overwrite versioning, lock/unlock collaborative safety mechanics, agent token creation/scoping, and verifying the Model Context Protocol (MCP) server integration using stdio and SSE transports.

---

## Prerequisites

Before starting, ensure that:
1. The development server dependencies are installed and migrations have been executed.
   ```bash
   python -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   ```
2. The server settings are configured (defaulting to SQLite locally if PostgreSQL variables are not specified in `.env`).
3. You have `curl` or a REST client (like Postman or Thunder Client) installed.

---

## User Journey 1: User Registration, Login, and Project Setup

This scenario verifies that human users can register, log in, and establish their authentication headers.

### Step 1: Register a New User
Send a POST request to register a user.

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev-human@lore.sh",
    "password": "SecurePassword123!",
    "first_name": "Dev",
    "last_name": "Human",
    "terms_agreement": true
  }'
```

**Expected Response (201 Created):**
```json
{
  "status": "success",
  "message": "Hi Dev, thank you for signing up.",
  "data": {
    "email": "dev-human@lore.sh",
    "first_name": "Dev",
    "last_name": "Human"
  }
}
```

### Step 2: Log In to Obtain JWT Tokens
Send a POST request with the credentials to login.

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev-human@lore.sh",
    "password": "SecurePassword123!"
  }'
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "id": "some-uuid-string",
    "email": "dev-human@lore.sh",
    "full_name": "Dev Human",
    "access_token": "YOUR_JWT_ACCESS_TOKEN",
    "refresh_token": "YOUR_JWT_REFRESH_TOKEN"
  }
}
```

> **Note:** For all subsequent requests requiring human authorization, pass the header:
> `Authorization: Bearer YOUR_JWT_ACCESS_TOKEN`

---

## User Journey 2: Directory & Folder Hierarchies

Verify creating a folder hierarchy and retrieving contents.

### Step 1: Create a Sandbox Directory
Let's create a root folder called `Agent Workspace`.

```bash
curl -X POST http://127.0.0.1:8000/api/folders/ \
  -H "Authorization: Bearer YOUR_JWT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Agent Workspace"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": "FOLDER_WORKSPACE_UUID",
  "name": "Agent Workspace",
  "slug": "agent-workspace",
  "created_at": "...",
  "updated_at": "...",
  "owner": "...",
  "folder": null
}
```

### Step 2: Create a Nested Subfolder
Create a subfolder named `Logs` inside `Agent Workspace`.

```bash
curl -X POST http://127.0.0.1:8000/api/folders/ \
  -H "Authorization: Bearer YOUR_JWT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Logs",
    "folder_id": "FOLDER_WORKSPACE_UUID"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": "FOLDER_LOGS_UUID",
  "name": "Logs",
  "slug": "logs",
  "created_at": "...",
  "updated_at": "...",
  "owner": "...",
  "folder": "FOLDER_WORKSPACE_UUID"
}
```

---

## User Journey 3: File Management, Overwriting, and Diff Generation

Verify file upload, version history tracking, and differential storage.

### Step 1: Upload an Initial Document
Upload a new file `task_report.md` into `Agent Workspace`.

```bash
curl -X POST http://127.0.0.1:8000/api/files/upload \
  -H "Authorization: Bearer YOUR_JWT_ACCESS_TOKEN" \
  -F "file=@-;filename=task_report.md" \
  -F "folder_id=FOLDER_WORKSPACE_UUID" <<EOF
# Task Report
Initial state: All tests pending.
EOF
```

**Expected Response (201 Created):**
```json
{
  "id": "FILE_REPORT_UUID",
  "name": "task_report.md",
  "folder": "FOLDER_WORKSPACE_UUID",
  "size": 39,
  "created_at": "...",
  "updated_at": "..."
}
```

### Step 2: Overwrite the Document to Create a Version History
Upload an updated version of `task_report.md` to the same folder.

```bash
curl -X POST http://127.0.0.1:8000/api/files/upload \
  -H "Authorization: Bearer YOUR_JWT_ACCESS_TOKEN" \
  -F "file=@-;filename=task_report.md" \
  -F "folder_id=FOLDER_WORKSPACE_UUID" <<EOF
# Task Report
Initial state: All tests passed.
EOF
```

**Expected Response (201 Created):**
Same file model returned, but internally a new `FileVersion` has been recorded.

### Step 3: Retrieve File Versions and Diffs
Fetch the version history of the file:

```bash
curl -X GET http://127.0.0.1:8000/api/files/FILE_REPORT_UUID/versions \
  -H "Authorization: Bearer YOUR_JWT_ACCESS_TOKEN"
```

**Expected Response (200 OK):**
```json
[
  {
    "id": "VERSION_UUID",
    "version_number": 1,
    "diff_content": "--- original\n+++ updated\n@@ -1,2 +1,2 @@\n # Task Report\n-Initial state: All tests pending.\n+Initial state: All tests passed.\n",
    "created_at": "...",
    "created_by": "dev-human@lore.sh"
  }
]
```

---

## User Journey 4: Collaborative File Locking

Verify concurrent access safety locks.

### Step 1: Lock the File
Lock `task_report.md` so that other processes or agents cannot write to it:

```bash
curl -X POST http://127.0.0.1:8000/api/files/FILE_REPORT_UUID/lock \
  -H "Authorization: Bearer YOUR_JWT_ACCESS_TOKEN"
```

**Expected Response (200 OK):**
Returns the file metadata showing `locked_by` filled.

### Step 2: Try to Overwrite/Modify the Locked File
To simulate a different user context, if another user (or an agent token with a different user context) attempts to overwrite `task_report.md`:

```bash
curl -X POST http://127.0.0.1:8000/api/files/upload \
  -H "Authorization: Bearer DIFFERENT_USER_TOKEN" \
  -F "file=@-;filename=task_report.md" \
  -F "folder_id=FOLDER_WORKSPACE_UUID" <<EOF
Malicious overwrite.
EOF
```

**Expected Response (403 Forbidden):**
```json
{
  "message": "File is locked by dev-human@lore.sh"
}
```

### Step 3: Unlock the File
Unlock it:

```bash
curl -X POST http://127.0.0.1:8000/api/files/FILE_REPORT_UUID/unlock \
  -H "Authorization: Bearer YOUR_JWT_ACCESS_TOKEN"
```

---

## User Journey 5: Agent Scoped Tokens

Create and verify scoped tokens for AI agents with sandboxed directory access.

### Step 1: Create a Sandboxed Token
Create a read-write agent token restricted specifically to the `Logs` directory (`FOLDER_LOGS_UUID`).

```bash
curl -X POST http://127.0.0.1:8000/api/auth/tokens \
  -H "Authorization: Bearer YOUR_JWT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Agent Sandbox Token",
    "scope": "read_write",
    "restricted_folder_id": "FOLDER_LOGS_UUID"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": "TOKEN_UUID",
  "token": "lore_agent_SOME_HEXADECIMAL_STRING",
  "token_prefix": "lore_agent_SOME_HEX",
  "description": "Agent Sandbox Token",
  "scope": "read_write",
  "restricted_folder": "FOLDER_LOGS_UUID",
  "created_at": "...",
  "expires_at": null
}
```

> **Important:** Save the plaintext `token` value (`lore_agent_...`). It is only returned once upon creation!

---

## User Journey 6: Model Context Protocol (MCP) Server Verification

Verify the MCP Server using the token created in Journey 5.

### Scenario A: stdio Transport Mode (Local agent connection)

1. Launch the stdio MCP server from your command line:
   ```bash
   python mcp_server.py --transport stdio --token lore_agent_SOME_HEXADECIMAL_STRING
   ```

2. The process will run and wait for JSON-RPC frames on stdin.
3. Test with standard JSON-RPC frames. Send a `list_tools` frame:
   ```json
   {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
   ```
   **Expected Response:** A JSON-RPC list response detailing `list_directory`, `read_document`, `write_document`, and `search_documents`.

4. Test sandboxed directory lookup. Send a call tool frame:
   ```json
   {
     "jsonrpc": "2.0",
     "method": "tools/call",
     "params": {
       "name": "list_directory",
       "arguments": {}
     },
     "id": 2
   }
   ```
   **Expected Response:** List containing contents inside `Logs` (the restricted sandboxed folder).

5. Test sandbox violation constraint. Try to list the parent `Agent Workspace` (`FOLDER_WORKSPACE_UUID`):
   ```json
   {
     "jsonrpc": "2.0",
     "method": "tools/call",
     "params": {
       "name": "list_directory",
       "arguments": {
         "folder_id": "FOLDER_WORKSPACE_UUID"
       }
     },
     "id": 3
   }
   ```
   **Expected Response:**
   ```json
   {
     "jsonrpc": "2.0",
     "result": {
       "content": [
         {
           "type": "text",
           "text": "Error: Access denied. Folder is outside sandboxed scope."
         }
       ]
     },
     "id": 3
   }
   ```

### Scenario B: SSE Transport Mode (HTTP/EventSource)

1. Run the SSE MCP server:
   ```bash
   python mcp_server.py --transport sse --port 8001
   ```

2. Test client handshake. Connect to the event stream using curl:
   ```bash
   curl -N "http://127.0.0.1:8001/sse?token=lore_agent_SOME_HEXADECIMAL_STRING"
   ```
   **Expected Output:** An open EventSource stream starting with:
   ```
   event: endpoint
   data: /messages?t=...
   ```

3. Extract the endpoint parameter from the response. Post tool calls using curl to that messages endpoint (e.g. `/messages?t=...`):
   ```bash
   curl -X POST "http://127.0.0.1:8001/messages?t=..." \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "method": "tools/list",
       "id": 1
     }'
   ```
   The result of the tool execution will be sent back through the open event stream.
