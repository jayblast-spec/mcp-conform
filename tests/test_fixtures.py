# SPDX-License-Identifier: Apache-2.0
"""The credibility test for this whole project: mcp-conform must report zero
FAILs against a genuinely compliant server, and it must catch every
violation deliberately planted in the broken fixture. A conformance tool
that can't tell the two apart is worthless — so this is the test that
actually matters, not a formality.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_conform.report import Status
from mcp_conform.runner import run

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
PYTHON = sys.executable


@pytest.mark.anyio
async def test_good_server_has_zero_failures():
    target = f'{PYTHON} "{FIXTURES / "good_server.py"}"'
    report = await run(target)
    failed = [r for r in report.results if r.status == Status.FAIL]
    assert failed == [], f"Compliant fixture reported FAILs: {[(r.check_id, r.detail) for r in failed]}"
    assert any(r.status == Status.PASS for r in report.results), "Expected at least some PASS results."


@pytest.mark.anyio
async def test_broken_server_invalid_tool_name_is_caught():
    target = f'{PYTHON} "{FIXTURES / "broken_server.py"}"'
    report = await run(target)
    by_id = {r.check_id: r for r in report.results}
    assert by_id["tools.invalid_name_handling"].status == Status.FAIL


@pytest.mark.anyio
async def test_broken_server_missing_required_args_is_caught():
    target = f'{PYTHON} "{FIXTURES / "broken_server.py"}"'
    report = await run(target)
    by_id = {r.check_id: r for r in report.results}
    assert by_id["tools.missing_required_args"].status == Status.FAIL


@pytest.mark.anyio
async def test_broken_server_resources_capability_mismatch_is_caught():
    target = f'{PYTHON} "{FIXTURES / "broken_server.py"}"'
    report = await run(target)
    by_id = {r.check_id: r for r in report.results}
    assert by_id["resources.capability_consistency"].status == Status.FAIL


@pytest.mark.anyio
async def test_broken_server_exit_code_is_nonzero():
    target = f'{PYTHON} "{FIXTURES / "broken_server.py"}"'
    report = await run(target)
    assert report.exit_code == 1


@pytest.mark.anyio
async def test_good_server_exit_code_is_zero():
    target = f'{PYTHON} "{FIXTURES / "good_server.py"}"'
    report = await run(target)
    assert report.exit_code == 0
