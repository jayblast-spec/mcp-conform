# SPDX-License-Identifier: Apache-2.0
"""CLI entrypoint: `mcp-conform <target>`.

<target> is either a shell command to launch a stdio MCP server
(e.g. "python server.py" run under stdio transport) or an http(s) URL for a
Streamable HTTP MCP server.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from .runner import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mcp-conform",
        description="Check an MCP server against the Model Context Protocol spec (2025-11-25+).",
    )
    parser.add_argument("target", help='An http(s) URL, or a quoted stdio launch command, e.g. "python server.py"')
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON instead of text.")
    args = parser.parse_args(argv)

    report = asyncio.run(run(args.target))

    print(report.to_json() if args.json else report.to_text())
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
