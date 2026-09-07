# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from .checks import SESSION_CHECKS
from .http_checks import HTTP_CHECKS
from .report import CheckResult, Report, Status
from .transport import Target, connect


async def run(target_str: str, cwd: str | None = None) -> Report:
    """cwd: working directory for a stdio launch command (e.g. a freshly
    cloned repo) — ignored for http(s) targets."""
    target = Target.parse(target_str, cwd=cwd)
    report = Report(target=target_str)

    try:
        async with connect(target) as (session, init):
            for check in SESSION_CHECKS:
                try:
                    result = await check(session, init)
                except Exception as exc:  # noqa: BLE001
                    result = CheckResult(
                        check.__name__, check.__name__, Status.ERROR,
                        f"Check raised unexpectedly: {type(exc).__name__}: {exc}",
                    )
                report.add(result)
    except Exception as exc:  # noqa: BLE001
        report.add(CheckResult(
            "connect", "connect and initialize a session with the target",
            Status.ERROR, f"{type(exc).__name__}: {exc}",
        ))
        return report

    if target.is_http:
        for check in HTTP_CHECKS:
            try:
                result = await check(target.raw)
            except Exception as exc:  # noqa: BLE001
                result = CheckResult(
                    check.__name__, check.__name__, Status.ERROR,
                    f"Check raised unexpectedly: {type(exc).__name__}: {exc}",
                )
            report.add(result)

    return report
