import argparse
import asyncio
import hashlib
import os
import sys
from uuid import UUID

# Setup Django environment before importing models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lore.settings.base")
import django

django.setup()

import mcp.types as types  # noqa: E402
from asgiref.sync import sync_to_async  # noqa: E402
from django.utils import timezone  # noqa: E402
from mcp.server.lowlevel import Server  # noqa: E402

from apps.accounts.models import AgentToken  # noqa: E402
from apps.files.models import File as FileModel  # noqa: E402
from apps.files.models import FileVersion  # noqa: E402
from apps.files.utils import compute_diff  # noqa: E402
from apps.folders.models import Folder  # noqa: E402

# --- Helper Database Operations ---

def authenticate_token(token_str: str) -> AgentToken | None:
    if not token_str or not token_str.startswith("lore_agent_"):
        return None
    token_hash = hashlib.sha256(token_str.encode()).hexdigest()
    try:
        agent_token = AgentToken.objects.select_related("user", "restricted_folder").get(
            token_hash=token_hash
        )
        if agent_token.expires_at and agent_token.expires_at < timezone.now():
            return None
        return agent_token
    except AgentToken.DoesNotExist:
        return None


def execute_list_directory(agent_token: AgentToken, folder_id: str | None = None) -> str:
    user = agent_token.user

    if agent_token.restricted_folder:
        allowed_folders = agent_token.restricted_folder.get_descendants(include_self=True)
        allowed_ids = [f.id for f in allowed_folders]

        if folder_id:
            try:
                target_uuid = UUID(folder_id)
            except ValueError:
                return "Error: Invalid folder UUID format."
            if target_uuid not in allowed_ids:
                return "Error: Access denied. Folder is outside sandboxed scope."
            target_folder = Folder.objects.get(id=target_uuid)
        else:
            target_folder = agent_token.restricted_folder
    else:
        if folder_id:
            try:
                target_uuid = UUID(folder_id)
            except ValueError:
                return "Error: Invalid folder UUID format."
            try:
                target_folder = Folder.objects.get(id=target_uuid, owner=user)
            except Folder.DoesNotExist:
                return "Error: Folder not found or access denied."
        else:
            target_folder = None

    subfolders = Folder.objects.filter(folder=target_folder, owner=user)
    files = FileModel.objects.filter(folder=target_folder, owner=user)

    output = [f"Directory contents for: {target_folder.name if target_folder else '/'}", "Subdirectories:"]
    for sf in subfolders:
        output.append(f" - [Folder] name: {sf.name}, id: {sf.id}")
    if not subfolders.exists():
        output.append(" (None)")

    output.append("Files:")
    for f in files:
        lock_status = f" (Locked by {f.locked_by.email})" if f.locked_by else ""
        output.append(f" - [File] name: {f.name}, id: {f.id}{lock_status}")
    if not files.exists():
        output.append(" (None)")

    return "\n".join(output)


def execute_read_document(agent_token: AgentToken, file_id: str) -> str:
    user = agent_token.user
    try:
        file_uuid = UUID(file_id)
    except ValueError:
        return "Error: Invalid file UUID format."

    try:
        file_obj = FileModel.objects.select_related("folder").get(id=file_uuid, owner=user)
    except FileModel.DoesNotExist:
        return "Error: File not found or access denied."

    if agent_token.restricted_folder:
        allowed_folders = agent_token.restricted_folder.get_descendants(include_self=True)
        allowed_ids = [f.id for f in allowed_folders]
        if not file_obj.folder or file_obj.folder.id not in allowed_ids:
            return "Error: Access denied. File is outside sandboxed scope."

    try:
        content = file_obj.file.read().decode("utf-8")
        file_obj.file.seek(0)
        return content
    except UnicodeDecodeError:
        return "[Binary file - cannot display content as text]"


def execute_write_document(agent_token: AgentToken, name: str, content: str, folder_id: str | None = None) -> str:
    user = agent_token.user
    from django.core.files.base import ContentFile

    if agent_token.restricted_folder:
        allowed_folders = agent_token.restricted_folder.get_descendants(include_self=True)
        allowed_ids = [f.id for f in allowed_folders]

        if folder_id:
            try:
                target_uuid = UUID(folder_id)
            except ValueError:
                return "Error: Invalid folder UUID format."
            if target_uuid not in allowed_ids:
                return "Error: Access denied. Folder is outside sandboxed scope."
            target_folder = Folder.objects.get(id=target_uuid)
        else:
            target_folder = agent_token.restricted_folder
    else:
        if folder_id:
            try:
                target_uuid = UUID(folder_id)
            except ValueError:
                return "Error: Invalid folder UUID format."
            try:
                target_folder = Folder.objects.get(id=target_uuid, owner=user)
            except Folder.DoesNotExist:
                return "Error: Folder not found or access denied."
        else:
            target_folder = None

    existing_file = FileModel.objects.filter(
        owner=user,
        name=name,
        folder=target_folder
    ).first()

    new_content_bytes = content.encode("utf-8")

    if existing_file:
        if existing_file.locked_by and existing_file.locked_by != user:
            return f"Error: File is locked by {existing_file.locked_by.email}."

        old_content = existing_file.file.read()
        existing_file.file.seek(0)

        version_number = existing_file.versions.count() + 1
        diff_str = compute_diff(old_content, new_content_bytes)

        FileVersion.objects.create(
            file=existing_file,
            version_number=version_number,
            file_instance=ContentFile(old_content, name=f"v{version_number}_{existing_file.name}"),
            diff_content=diff_str,
            created_by=user
        )

        existing_file.file.save(name, ContentFile(new_content_bytes), save=False)
        existing_file.save()
        return f"File '{name}' overwritten successfully. Created version {version_number}."

    FileModel.objects.create(
        owner=user,
        name=name,
        file=ContentFile(new_content_bytes, name=name),
        folder=target_folder
    )
    return f"File '{name}' created successfully."


def execute_search_documents(agent_token: AgentToken, query: str) -> str:
    user = agent_token.user

    files_qs = FileModel.objects.filter(owner=user).select_related("folder")
    folders_qs = Folder.objects.filter(owner=user)

    if agent_token.restricted_folder:
        allowed_folders = agent_token.restricted_folder.get_descendants(include_self=True)
        allowed_ids = [f.id for f in allowed_folders]
        files_qs = files_qs.filter(folder_id__in=allowed_ids)
        folders_qs = folders_qs.filter(id__in=allowed_ids)

    matched_files = files_qs.filter(name__icontains=query)
    matched_folders = folders_qs.filter(name__icontains=query)

    output = [f"Search results for: '{query}'", "Matched folders:"]
    for f in matched_folders:
        output.append(f" - [Folder] name: {f.name}, id: {f.id}")
    if not matched_folders.exists():
        output.append(" (None)")

    output.append("Matched files:")
    for f in matched_files:
        output.append(f" - [File] name: {f.name}, id: {f.id}")

    content_matches = []
    for file_obj in files_qs:
        if file_obj in matched_files:
            continue
        try:
            content = file_obj.file.read()
            file_obj.file.seek(0)
            text = content.decode("utf-8")
            if query.lower() in text.lower():
                content_matches.append(file_obj)
        except Exception:
            pass

    if content_matches:
        output.append("Matched file contents:")
        for f in content_matches:
            output.append(f" - [File Content Match] name: {f.name}, id: {f.id}")

    if not matched_files.exists() and not content_matches:
        output.append(" (None)")

    return "\n".join(output)


# --- MCP Server Factory ---

def create_server_for_token(agent_token: AgentToken) -> Server:
    server = Server("lore-mcp-server")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="list_directory",
                description="List files and subfolders inside a target directory.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "Optional UUID of the folder."}
                    }
                }
            ),
            types.Tool(
                name="read_document",
                description="Retrieve text contents of a file.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string", "description": "The UUID of the file."}
                    },
                    "required": ["file_id"]
                }
            ),
            types.Tool(
                name="write_document",
                description="Write or overwrite a document. Automatically creates new file versions and unified text diffs on overwrite.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "The name of the file (e.g. config.txt)."},
                        "content": {"type": "string", "description": "The text content of the file."},
                        "folder_id": {"type": "string", "description": "Optional UUID of the parent folder."}
                    },
                    "required": ["name", "content"]
                }
            ),
            types.Tool(
                name="search_documents",
                description="Search documents inside the vault by name or content text.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search term."}
                    },
                    "required": ["query"]
                }
            )
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str,
        arguments: dict | None
    ) -> list[types.TextContent]:
        if agent_token.scope == "read_only" and name in ("write_document",):
            return [types.TextContent(
                type="text",
                text="Error: Token scope 'read_only' does not permit this operation."
            )]

        try:
            if name == "list_directory":
                folder_id = (arguments or {}).get("folder_id")
                result = await sync_to_async(execute_list_directory)(agent_token, folder_id)
                return [types.TextContent(type="text", text=result)]
            elif name == "read_document":
                file_id = (arguments or {}).get("file_id")
                result = await sync_to_async(execute_read_document)(agent_token, file_id)
                return [types.TextContent(type="text", text=result)]
            elif name == "write_document":
                file_name = (arguments or {}).get("name")
                content = (arguments or {}).get("content")
                folder_id = (arguments or {}).get("folder_id")
                result = await sync_to_async(execute_write_document)(agent_token, file_name, content, folder_id)
                return [types.TextContent(type="text", text=result)]
            elif name == "search_documents":
                query = (arguments or {}).get("query")
                result = await sync_to_async(execute_search_documents)(agent_token, query)
                return [types.TextContent(type="text", text=result)]
            else:
                return [types.TextContent(type="text", text=f"Error: Unknown tool '{name}'")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error executing tool: {str(e)}")]

    return server


# --- Transport Runners ---

async def run_stdio(token_str: str):
    agent_token = await sync_to_async(authenticate_token)(token_str)
    if not agent_token:
        print(f"Error: Invalid or expired token '{token_str}'", file=sys.stderr)
        sys.exit(1)

    from mcp.server.stdio import stdio_server
    server = create_server_for_token(agent_token)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def run_sse(host: str, port: int):
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

    sse = SseServerTransport("/messages")

    async def handle_sse(request):
        token = request.query_params.get("token") or request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token[7:]

        agent_token = await sync_to_async(authenticate_token)(token)
        if not agent_token:
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as (read_stream, write_stream):
            server = create_server_for_token(agent_token)
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    routes = [
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages", app=sse.handle_post_message),
    ]

    app = Starlette(routes=routes)
    uvicorn.run(app, host=host, port=port)


# --- Main CLI Entrypoint ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lore Model Context Protocol (MCP) Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="Transport mechanism")
    parser.add_argument("--host", default="127.0.0.1", help="SSE host address")
    parser.add_argument("--port", type=int, default=8001, help="SSE port number")
    parser.add_argument("--token", help="Plaintext agent token for authentication (required for stdio)")

    args = parser.parse_args()

    if args.transport == "stdio":
        if not args.token:
            print("Error: --token is required when running in stdio transport mode.", file=sys.stderr)
            sys.exit(1)
        asyncio.run(run_stdio(args.token))
    elif args.transport == "sse":
        run_sse(args.host, args.port)
