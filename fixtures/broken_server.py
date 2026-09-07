# SPDX-License-Identifier: Apache-2.0
"""A deliberately non-compliant MCP server — the negative control fixture.

Built on the low-level Server API (bypassing FastMCP's own correct defaults)
specifically so it misbehaves in ways mcp-conform's checks are supposed to
catch. If mcp-conform reports zero FAILs against this, the checks are
worthless and need fixing.

Violations planted on purpose:
1. call_tool always "succeeds" (isError never set), even for an unknown tool
   name or missing required arguments.
2. Declares a resources capability, but resources/list raises.
3. resources/templates/list also raises.
"""

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

server = Server("broken-server")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="add",
            description="Add two integers.",
            inputSchema={
                "type": "object",
                "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                "required": ["a", "b"],
            },
        )
    ]


@server.call_tool(validate_input=False)
async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
    # Violation: no error path at all — unknown tool names and missing
    # required arguments both silently "succeed".
    return [types.TextContent(type="text", text=f"ok: called {name!r} with {arguments!r}")]


@server.list_resources()
async def list_resources() -> list[types.Resource]:
    raise RuntimeError("intentionally broken: resources capability declared but list_resources crashes")


@server.list_resource_templates()
async def list_resource_templates() -> list[types.ResourceTemplate]:
    raise RuntimeError("intentionally broken: resources/templates/list crashes too")


async def _run() -> None:
    init_options = server.create_initialization_options()
    async with stdio_server() as (read, write):
        await server.run(read, write, init_options)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run())
