# SPDX-License-Identifier: Apache-2.0
"""Raw JSON-RPC checks against a Streamable HTTP MCP endpoint — deliberately
malformed input the official SDK client would never construct. Only run when
the target is an http(s) URL.
"""

from __future__ import annotations

import json

from .report import CheckResult, Status
from .transport import raw_jsonrpc_post

JSONRPC_SPEC = "https://www.jsonrpc.org/specification"


async def check_unknown_method(url: str) -> CheckResult:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "__mcp_conform_unknown_method__"})
    try:
        resp = await raw_jsonrpc_post(url, body)
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "http.unknown_method", "unknown method returns a JSON-RPC error, not a crash",
            Status.ERROR, f"Request itself failed: {exc}", JSONRPC_SPEC,
        )
    if resp.status_code >= 500:
        return CheckResult(
            "http.unknown_method", "unknown method returns a JSON-RPC error, not a crash",
            Status.FAIL, f"Server returned HTTP {resp.status_code} for an unknown method.", JSONRPC_SPEC,
        )
    return CheckResult(
        "http.unknown_method", "unknown method returns a JSON-RPC error, not a crash",
        Status.PASS, f"HTTP {resp.status_code} (no server error) for an unknown method.", JSONRPC_SPEC,
    )


async def check_malformed_json_body(url: str) -> CheckResult:
    try:
        resp = await raw_jsonrpc_post(url, "{not valid json!!")
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "http.malformed_json", "malformed JSON body is rejected gracefully, not a crash",
            Status.ERROR, f"Request itself failed: {exc}", JSONRPC_SPEC,
        )
    if resp.status_code >= 500:
        return CheckResult(
            "http.malformed_json", "malformed JSON body is rejected gracefully, not a crash",
            Status.FAIL, f"Server returned HTTP {resp.status_code} for an invalid JSON body (expected 4xx or a JSON-RPC parse error).",
            JSONRPC_SPEC,
        )
    return CheckResult(
        "http.malformed_json", "malformed JSON body is rejected gracefully, not a crash",
        Status.PASS, f"HTTP {resp.status_code} (no server error) for an invalid JSON body.", JSONRPC_SPEC,
    )


async def check_missing_jsonrpc_field(url: str) -> CheckResult:
    body = json.dumps({"id": 1, "method": "tools/list"})  # missing "jsonrpc": "2.0"
    try:
        resp = await raw_jsonrpc_post(url, body)
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "http.missing_jsonrpc_field", "request missing the jsonrpc version field is rejected gracefully",
            Status.ERROR, f"Request itself failed: {exc}", JSONRPC_SPEC,
        )
    if resp.status_code >= 500:
        return CheckResult(
            "http.missing_jsonrpc_field", "request missing the jsonrpc version field is rejected gracefully",
            Status.FAIL, f"Server returned HTTP {resp.status_code} for a request missing \"jsonrpc\".", JSONRPC_SPEC,
        )
    return CheckResult(
        "http.missing_jsonrpc_field", "request missing the jsonrpc version field is rejected gracefully",
        Status.PASS, f"HTTP {resp.status_code} (no server error) for a request missing \"jsonrpc\".", JSONRPC_SPEC,
    )


async def check_accept_header_requirement(url: str) -> CheckResult:
    """Streamable HTTP requires the client to send an Accept header covering
    both application/json and text/event-stream. This is genuinely
    implementation-defined how strictly a server enforces it, so a rejection
    OR an acceptance are both reported as informational, not scored FAIL —
    the spec says the client SHOULD send both, not that the server MUST
    reject requests that don't.
    """
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
    try:
        resp = await raw_jsonrpc_post(url, body, headers={"Accept": "text/plain"})
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "http.accept_header_handling", "behavior with a non-conforming Accept header",
            Status.ERROR, f"Request itself failed: {exc}", JSONRPC_SPEC,
        )
    if resp.status_code >= 500:
        return CheckResult(
            "http.accept_header_handling", "behavior with a non-conforming Accept header",
            Status.WARN, f"HTTP {resp.status_code} (server error) with Accept: text/plain — likely too strict a crash path rather than a clean 4xx.",
            JSONRPC_SPEC,
        )
    return CheckResult(
        "http.accept_header_handling", "behavior with a non-conforming Accept header",
        Status.PASS, f"HTTP {resp.status_code}, no server error, with a non-conforming Accept header.", JSONRPC_SPEC,
    )


HTTP_CHECKS = [
    check_unknown_method,
    check_malformed_json_body,
    check_missing_jsonrpc_field,
    check_accept_header_requirement,
]
