# SPDX-License-Identifier: Apache-2.0
"""A minimal, fully spec-compliant MCP server — the positive control fixture.
mcp-conform should report zero FAILs against this."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("good-server")


@mcp.tool()
def add(a: int, b: int) -> str:
    """Add two integers."""
    return str(a + b)


@mcp.resource("test://greeting")
def greeting() -> str:
    """A static greeting resource."""
    return "hello from a compliant resource"


@mcp.prompt()
def greet(name: str) -> str:
    """A minimal prompt template."""
    return f"Say hello to {name}."


if __name__ == "__main__":
    mcp.run(transport="stdio")
