# SPDX-License-Identifier: Apache-2.0
"""Connects to a target MCP server two ways:

1. A polite `mcp.ClientSession` (via stdio subprocess or Streamable HTTP) —
   used for checks that exercise the protocol the way a real client would.
2. Raw JSON-RPC over HTTP (httpx directly, bypassing the SDK) — used for
   checks that need to send deliberately malformed input the SDK itself
   would refuse to construct (that's the SDK doing its job; a conformance
   tool has to be willing to misbehave on purpose).

A target is either a shell command (stdio) or an http(s) URL (Streamable HTTP).
"""

from __future__ import annotations

import os
import shlex
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client


def _split_command(raw: str) -> list[str]:
    """Splits a shell-like command string into argv, correctly on both
    platforms. posix-mode shlex treats backslashes as escape characters,
    which mangles Windows paths (`C:\\Users\\...\\python.exe`) — so on
    Windows this splits in non-posix mode and then strips any surrounding
    quote characters non-posix mode otherwise leaves in each token.
    """
    if os.name == "nt":
        return [p[1:-1] if len(p) >= 2 and p[0] == p[-1] == '"' else p for p in shlex.split(raw, posix=False)]
    return shlex.split(raw)


@dataclass
class Target:
    raw: str
    is_http: bool

    @classmethod
    def parse(cls, raw: str) -> "Target":
        return cls(raw=raw, is_http=raw.startswith("http://") or raw.startswith("https://"))


@asynccontextmanager
async def connect(target: Target):
    """Yields (session, init_result) for the target — init_result is captured
    explicitly here since ClientSession doesn't reliably expose it publicly
    across SDK versions."""
    if target.is_http:
        async with streamablehttp_client(target.raw) as (read, write, _):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                yield session, init
    else:
        parts = _split_command(target.raw)
        params = StdioServerParameters(command=parts[0], args=parts[1:])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                yield session, init


async def raw_jsonrpc_post(url: str, body: bytes | str, headers: dict | None = None) -> httpx.Response:
    """Sends a raw HTTP POST to an MCP Streamable HTTP endpoint, bypassing the
    SDK entirely — for tests that need to send invalid JSON-RPC on purpose.
    """
    merged_headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if headers:
        merged_headers.update(headers)
    async with httpx.AsyncClient(timeout=10.0) as client:
        data = body.encode() if isinstance(body, str) else body
        return await client.post(url, content=data, headers=merged_headers)
