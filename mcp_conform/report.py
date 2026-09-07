# SPDX-License-Identifier: Apache-2.0
"""Result types and report rendering — kept separate from check logic so a
check never has to know how its result will be displayed or scored."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"   # spec-legal either way, or ambiguous — surfaced, not scored as failure
    SKIP = "SKIP"   # not applicable (e.g. capability not declared)
    ERROR = "ERROR"  # the check itself couldn't run (transport/connection problem)


@dataclass
class CheckResult:
    check_id: str
    name: str
    status: Status
    detail: str
    spec_ref: str = ""


@dataclass
class Report:
    target: str
    results: list[CheckResult] = field(default_factory=list)

    def add(self, result: CheckResult) -> None:
        self.results.append(result)

    @property
    def failed(self) -> list[CheckResult]:
        return [r for r in self.results if r.status == Status.FAIL]

    @property
    def errored(self) -> list[CheckResult]:
        return [r for r in self.results if r.status == Status.ERROR]

    @property
    def exit_code(self) -> int:
        """Non-zero if anything actually failed or errored — designed to be
        used as a CI gate (`mcp-conform ... || exit 1`)."""
        return 1 if (self.failed or self.errored) else 0

    def to_json(self) -> str:
        return json.dumps(
            {
                "target": self.target,
                "summary": {
                    "pass": sum(1 for r in self.results if r.status == Status.PASS),
                    "fail": len(self.failed),
                    "warn": sum(1 for r in self.results if r.status == Status.WARN),
                    "skip": sum(1 for r in self.results if r.status == Status.SKIP),
                    "error": len(self.errored),
                },
                "results": [
                    {
                        "id": r.check_id, "name": r.name, "status": r.status.value,
                        "detail": r.detail, "spec_ref": r.spec_ref,
                    }
                    for r in self.results
                ],
            },
            indent=2,
        )

    def to_text(self) -> str:
        icon = {
            Status.PASS: "PASS", Status.FAIL: "FAIL", Status.WARN: "WARN",
            Status.SKIP: "SKIP", Status.ERROR: "ERR ",
        }
        lines = [f"mcp-conform report for {self.target}", ""]
        for r in self.results:
            lines.append(f"[{icon[r.status]}] {r.check_id}: {r.name}")
            if r.detail:
                lines.append(f"       {r.detail}")
            if r.spec_ref:
                lines.append(f"       spec: {r.spec_ref}")
        lines.append("")
        lines.append(
            f"{sum(1 for r in self.results if r.status == Status.PASS)} passed, "
            f"{len(self.failed)} failed, "
            f"{sum(1 for r in self.results if r.status == Status.WARN)} warned, "
            f"{sum(1 for r in self.results if r.status == Status.SKIP)} skipped, "
            f"{len(self.errored)} errored"
        )
        return "\n".join(lines)
