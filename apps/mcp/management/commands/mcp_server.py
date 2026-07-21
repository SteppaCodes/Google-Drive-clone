import json
import sys
from django.core.management.base import BaseCommand
from apps.accounts.models import AgentToken, Principal
from apps.mcp.api import MCP_TOOLS_SPEC
from apps.mcp.tools import (
    mcp_create_relationship,
    mcp_list_collection,
    mcp_list_skills,
    mcp_read_artifact,
    mcp_revert_artifact,
    mcp_search_artifacts,
    mcp_write_artifact,
)


class MockRequest:
    def __init__(self, principal, agent_token=None):
        self.principal = principal
        self.user = principal.user if principal and principal.kind == "user" else None
        self.agent_token = agent_token


class Command(BaseCommand):
    help = "Run the Lore Model Context Protocol (MCP) server over stdio"

    def add_arguments(self, parser):
        parser.add_argument("--token", type=str, help="Lore Agent Token for authentication")

    def handle(self, *args, **options):
        token_str = options.get("token")
        request = None

        if token_str:
            import hashlib
            tok_hash = hashlib.sha256(token_str.encode()).hexdigest()
            tok = AgentToken.objects.filter(token_hash=tok_hash).first()
            if tok:
                request = MockRequest(principal=tok.principal, agent_token=tok)

        if not request:
            admin_p = Principal.objects.filter(kind="user").first()
            if admin_p:
                request = MockRequest(principal=admin_p)

        self.stderr.write("Lore MCP Server running on stdio...")

        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                method = payload.get("method")
                rpc_id = payload.get("id")
                params = payload.get("params", {})

                if method == "tools/list":
                    res = {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": MCP_TOOLS_SPEC}}
                elif method == "tools/call":
                    name = params.get("name")
                    arguments = params.get("arguments", {})

                    if name == "search_artifacts":
                        result = mcp_search_artifacts(request, **arguments)
                    elif name == "read_artifact":
                        result = mcp_read_artifact(request, **arguments)
                    elif name == "write_artifact":
                        result = mcp_write_artifact(request, **arguments)
                    elif name == "revert_artifact":
                        result = mcp_revert_artifact(request, **arguments)
                    elif name == "list_collection":
                        result = mcp_list_collection(request, **arguments)
                    elif name == "create_relationship":
                        result = mcp_create_relationship(request, **arguments)
                    elif name == "list_skills":
                        result = mcp_list_skills(request)
                    else:
                        result = {"error": f"Unknown tool {name}"}

                    res = {"jsonrpc": "2.0", "id": rpc_id, "result": {"content": [{"type": "text", "text": str(result)}]}}
                else:
                    res = {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": f"Unknown method {method}"}}

                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_res = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
                sys.stdout.write(json.dumps(err_res) + "\n")
                sys.stdout.flush()
