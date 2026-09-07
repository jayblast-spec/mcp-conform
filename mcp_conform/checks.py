# SPDX-License-Identifier: Apache-2.0
"""Individual compliance checks against the MCP spec (2025-11-25+).

Each check is a small async function: (session, InitializeResult) -> CheckResult.
Kept deliberately conservative — where the spec is genuinely ambiguous or a
choice is legitimately implementation-defined, a check reports WARN/INFO
rather than a hard FAIL with false confidence. A conformance tool that cries
wolf is worse than no conformance tool.
"""

from __future__ import annotations

from mcp.types import InitializeResult

from .report import CheckResult, Status

PROTOCOL_VERSION_SPEC = "https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle"
TOOLS_SPEC = "https://modelcontextprotocol.io/specification/2025-11-25/server/tools"
RESOURCES_SPEC = "https://modelcontextprotocol.io/specification/2025-11-25/server/resources"
PROMPTS_SPEC = "https://modelcontextprotocol.io/specification/2025-11-25/server/prompts"


async def check_initialize_result(session, init: InitializeResult) -> CheckResult:
    missing = []
    if not init.protocolVersion:
        missing.append("protocolVersion")
    if not init.serverInfo or not init.serverInfo.name:
        missing.append("serverInfo.name")
    if init.capabilities is None:
        missing.append("capabilities")
    if missing:
        return CheckResult(
            "initialize.required_fields", "initialize response has required fields",
            Status.FAIL, f"Missing: {', '.join(missing)}", PROTOCOL_VERSION_SPEC,
        )
    return CheckResult(
        "initialize.required_fields", "initialize response has required fields",
        Status.PASS, f"protocolVersion={init.protocolVersion!r}, server={init.serverInfo.name!r}",
        PROTOCOL_VERSION_SPEC,
    )


async def check_protocol_version_format(session, init: InitializeResult) -> CheckResult:
    version = init.protocolVersion
    # MCP protocol versions are dated (YYYY-MM-DD); this is a shape check,
    # not a claim about which specific versions are "valid" — the spec adds
    # new dated versions over time and this tool shouldn't hardcode a list.
    import re
    if not version or not re.match(r"^\d{4}-\d{2}-\d{2}$", version):
        return CheckResult(
            "initialize.protocol_version_format", "protocolVersion looks like a spec date",
            Status.WARN, f"Got {version!r}, expected YYYY-MM-DD shape.", PROTOCOL_VERSION_SPEC,
        )
    return CheckResult(
        "initialize.protocol_version_format", "protocolVersion looks like a spec date",
        Status.PASS, version, PROTOCOL_VERSION_SPEC,
    )


async def check_tools_capability_consistency(session, init: InitializeResult) -> CheckResult:
    declares_tools = bool(init.capabilities and init.capabilities.tools is not None)
    if not declares_tools:
        return CheckResult(
            "tools.capability_consistency", "tools capability matches tools/list behavior",
            Status.SKIP, "Server does not declare a tools capability.", TOOLS_SPEC,
        )
    try:
        result = await session.list_tools()
    except Exception as exc:  # noqa: BLE001 — any failure here is the finding
        return CheckResult(
            "tools.capability_consistency", "tools capability matches tools/list behavior",
            Status.FAIL, f"Declared tools capability but tools/list raised: {exc}", TOOLS_SPEC,
        )
    bad = [t.name for t in result.tools if not t.name or t.inputSchema is None]
    if bad:
        return CheckResult(
            "tools.capability_consistency", "tools capability matches tools/list behavior",
            Status.FAIL, f"Tool(s) missing name/inputSchema: {bad}", TOOLS_SPEC,
        )
    return CheckResult(
        "tools.capability_consistency", "tools capability matches tools/list behavior",
        Status.PASS, f"{len(result.tools)} tool(s), each with name + inputSchema.", TOOLS_SPEC,
    )


async def check_tool_call_invalid_name(session, init: InitializeResult) -> CheckResult:
    if not (init.capabilities and init.capabilities.tools is not None):
        return CheckResult(
            "tools.invalid_name_handling", "calling a nonexistent tool fails gracefully",
            Status.SKIP, "No tools capability.", TOOLS_SPEC,
        )
    bogus_name = "__mcp_conform_nonexistent_tool__"
    try:
        result = await session.call_tool(bogus_name, {})
    except Exception as exc:  # noqa: BLE001
        # A raised protocol-level error (e.g. JSON-RPC error) is also an
        # acceptable graceful failure mode — only a hang/crash is a real FAIL,
        # and an exception here means the transport didn't hang.
        return CheckResult(
            "tools.invalid_name_handling", "calling a nonexistent tool fails gracefully",
            Status.PASS, f"Raised a protocol-level error rather than crashing: {type(exc).__name__}", TOOLS_SPEC,
        )
    if not result.isError:
        return CheckResult(
            "tools.invalid_name_handling", "calling a nonexistent tool fails gracefully",
            Status.FAIL, "call_tool on a nonexistent name returned isError=False.", TOOLS_SPEC,
        )
    return CheckResult(
        "tools.invalid_name_handling", "calling a nonexistent tool fails gracefully",
        Status.PASS, "Returned CallToolResult(isError=True) as expected.", TOOLS_SPEC,
    )


async def check_tool_call_missing_required_args(session, init: InitializeResult) -> CheckResult:
    if not (init.capabilities and init.capabilities.tools is not None):
        return CheckResult(
            "tools.missing_required_args", "calling a tool without required args fails gracefully",
            Status.SKIP, "No tools capability.", TOOLS_SPEC,
        )
    tools = (await session.list_tools()).tools
    target = next(
        (t for t in tools if t.inputSchema and t.inputSchema.get("required")), None
    )
    if target is None:
        return CheckResult(
            "tools.missing_required_args", "calling a tool without required args fails gracefully",
            Status.SKIP, "No tool declares required arguments to test against.", TOOLS_SPEC,
        )
    try:
        result = await session.call_tool(target.name, {})
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "tools.missing_required_args", "calling a tool without required args fails gracefully",
            Status.PASS, f"Raised a protocol-level error rather than crashing: {type(exc).__name__}", TOOLS_SPEC,
        )
    if not result.isError:
        return CheckResult(
            "tools.missing_required_args", "calling a tool without required args fails gracefully",
            Status.FAIL, f"{target.name!r} requires {target.inputSchema['required']} but omitting them returned isError=False.",
            TOOLS_SPEC,
        )
    return CheckResult(
        "tools.missing_required_args", "calling a tool without required args fails gracefully",
        Status.PASS, f"{target.name!r} returned isError=True when required args were omitted.", TOOLS_SPEC,
    )


async def check_resources_capability_consistency(session, init: InitializeResult) -> CheckResult:
    if not (init.capabilities and init.capabilities.resources is not None):
        return CheckResult(
            "resources.capability_consistency", "resources capability matches resources/list behavior",
            Status.SKIP, "Server does not declare a resources capability.", RESOURCES_SPEC,
        )
    try:
        result = await session.list_resources()
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "resources.capability_consistency", "resources capability matches resources/list behavior",
            Status.FAIL, f"Declared resources capability but resources/list raised: {exc}", RESOURCES_SPEC,
        )
    if not result.resources:
        return CheckResult(
            "resources.capability_consistency", "resources capability matches resources/list behavior",
            Status.WARN, "resources/list succeeded but returned zero resources.", RESOURCES_SPEC,
        )
    first = result.resources[0]
    try:
        read = await session.read_resource(first.uri)
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "resources.capability_consistency", "resources capability matches resources/list behavior",
            Status.FAIL, f"Listed resource {first.uri} but reading it raised: {exc}", RESOURCES_SPEC,
        )
    if not read.contents or not any((c.text or getattr(c, "blob", None)) for c in read.contents):
        return CheckResult(
            "resources.capability_consistency", "resources capability matches resources/list behavior",
            Status.FAIL, f"Reading {first.uri} returned no text/blob content.", RESOURCES_SPEC,
        )
    return CheckResult(
        "resources.capability_consistency", "resources capability matches resources/list behavior",
        Status.PASS, f"{len(result.resources)} resource(s); {first.uri} reads with content.", RESOURCES_SPEC,
    )


async def check_prompts_capability_consistency(session, init: InitializeResult) -> CheckResult:
    if not (init.capabilities and init.capabilities.prompts is not None):
        return CheckResult(
            "prompts.capability_consistency", "prompts capability matches prompts/list behavior",
            Status.SKIP, "Server does not declare a prompts capability.", PROMPTS_SPEC,
        )
    try:
        result = await session.list_prompts()
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "prompts.capability_consistency", "prompts capability matches prompts/list behavior",
            Status.FAIL, f"Declared prompts capability but prompts/list raised: {exc}", PROMPTS_SPEC,
        )
    if not result.prompts:
        return CheckResult(
            "prompts.capability_consistency", "prompts capability matches prompts/list behavior",
            Status.WARN, "prompts/list succeeded but returned zero prompts.", PROMPTS_SPEC,
        )
    first = result.prompts[0]
    args = {a.name: "test" for a in (first.arguments or []) if a.required}
    try:
        got = await session.get_prompt(first.name, args or None)
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "prompts.capability_consistency", "prompts capability matches prompts/list behavior",
            Status.FAIL, f"Listed prompt {first.name!r} but get_prompt raised: {exc}", PROMPTS_SPEC,
        )
    if not got.messages:
        return CheckResult(
            "prompts.capability_consistency", "prompts capability matches prompts/list behavior",
            Status.FAIL, f"get_prompt({first.name!r}) returned zero messages.", PROMPTS_SPEC,
        )
    return CheckResult(
        "prompts.capability_consistency", "prompts capability matches prompts/list behavior",
        Status.PASS, f"{len(result.prompts)} prompt(s); {first.name!r} returns messages.", PROMPTS_SPEC,
    )


# Checks that need a session + init result (run for every target).
SESSION_CHECKS = [
    check_initialize_result,
    check_protocol_version_format,
    check_tools_capability_consistency,
    check_tool_call_invalid_name,
    check_tool_call_missing_required_args,
    check_resources_capability_consistency,
    check_prompts_capability_consistency,
]
