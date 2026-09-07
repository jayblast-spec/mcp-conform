<div align="center">

# mcp-conform

### The Compliance Gate For MCP Servers

mcp-conform runs a real MCP client against your server — over stdio or Streamable HTTP — and checks it against the Model Context Protocol spec (2025-11-25+): capability declarations must match actual behavior, tool/resource/prompt calls must fail gracefully instead of crashing or silently succeeding, and the JSON-RPC transport must handle malformed input the way the spec expects. It ships with a deliberately broken reference server and asserts every planted violation gets caught — a conformance tool that always says "pass" is worse than no tool at all.

<p>
  <a href="https://github.com/jayblast-spec/mcp-conform/actions/workflows/test.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/jayblast-spec/mcp-conform/test.yml?branch=master&style=for-the-badge&logo=githubactions&logoColor=white&label=CI&color=1D4ED8"></a>
  <a href="https://github.com/jayblast-spec/mcp-conform"><img alt="GitHub Repo" src="https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white"></a>
</p>

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python%203.10+-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="MCP" src="https://img.shields.io/badge/Model%20Context%20Protocol-1D4ED8?style=flat-square&logo=anthropic&logoColor=white">
  <img alt="httpx" src="https://img.shields.io/badge/httpx-1D4ED8?style=flat-square&logo=python&logoColor=white">
  <img alt="pytest" src="https://img.shields.io/badge/pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white">
  <img alt="GitHub Actions" src="https://img.shields.io/badge/GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/Apache%202.0-1D4ED8?style=flat-square&logo=apache&logoColor=white">
</p>

<p>
  <img alt="Animated mcp-conform headline" src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=18&duration=2600&pause=650&color=1D4ED8&center=true&vCenter=true&width=760&lines=Verify+the+spec+before+Alexa%2B+does;stdio+and+Streamable+HTTP%2C+one+CLI;Proven+against+a+deliberately+broken+server;Zero+FAILs+or+it+doesn%27t+ship">
</p>

</div>

## What It Does

MCP just became the wire protocol every major agent platform is racing to standardize on — Alexa+ among them — but there was no widely-used open-source tool that actually verified a server implements the spec correctly before shipping it. mcp-conform closes that gap: point it at any MCP server, stdio or Streamable HTTP, and it runs a real client session against it, checking that every capability the server *declares* it has actually *works* the way the spec requires, and that it fails gracefully — not silently or by crashing — on bad input. It returns a clean pass/fail report and a CI-ready exit code.

## How It Works

- `mcp_conform/transport.py` connects to a target two ways: a real `mcp.ClientSession` (stdio subprocess or Streamable HTTP) for protocol-correct checks, and raw `httpx` JSON-RPC posts for checks that need to send input the official SDK would refuse to construct.
- `mcp_conform/checks.py` runs the protocol-level checks against every target: `initialize` shape, capability-vs-behavior consistency for tools/resources/prompts, and graceful failure on an unknown tool name or missing required arguments.
- `mcp_conform/http_checks.py` runs HTTP-only checks: unknown methods, malformed JSON bodies, missing `jsonrpc` fields, and non-conforming `Accept` headers — all against the raw transport, on purpose.
- `mcp_conform/report.py` scores results as `PASS`/`FAIL`/`WARN`/`SKIP`/`ERROR` and renders text or JSON; exit code is non-zero only on a real `FAIL` or `ERROR`.
- `fixtures/good_server.py` and `fixtures/broken_server.py` are the positive and negative controls; `tests/test_fixtures.py` asserts zero FAILs against the first and all three planted violations caught in the second — this is what actually proves the tool works, not a formality.

## Install & Use

```bash
pip install -e .

mcp-conform "python my_server.py"              # stdio server
mcp-conform https://my-server.example.com/mcp  # Streamable HTTP server
mcp-conform "python my_server.py" --json       # machine-readable, for CI
```

Not yet published to PyPI — install from source for now.

## Repository

[github.com/jayblast-spec/mcp-conform](https://github.com/jayblast-spec/mcp-conform)

## Tech Stack

| Layer | Technology |
|---|---|
| Protocol | Model Context Protocol (spec 2025-11-25+) |
| Language | Python 3.10+ |
| MCP client | `mcp[cli]` (official SDK) |
| Raw transport checks | httpx |
| Tests | pytest + anyio |
| CI | GitHub Actions (Ubuntu + Windows, Python 3.10 + 3.12) |

## Run The Test Suite Yourself

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## License

Apache 2.0 — see [LICENSE](./LICENSE).

<div align="center">

<img alt="Footer" src="https://capsule-render.vercel.app/api?type=rect&height=60&color=0:1D4ED8,55:0B1E3D,100:020617&text=michael%40arknet.digital&fontColor=FAFAFA&fontSize=18&fontAlign=50&animation=fadeIn">

</div>
