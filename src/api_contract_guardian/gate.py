"""CI gate — determine if a spec change should pass or fail a CI pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .diff import DiffResult


@dataclass
class GateResult:
    """Result of a CI gate check."""

    passed: bool
    breaking_count: int
    dangerous_count: int
    message: str
    exit_code: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "breaking_count": self.breaking_count,
            "dangerous_count": self.dangerous_count,
            "message": self.message,
            "exit_code": self.exit_code,
        }


def check_gate(
    result: DiffResult,
    *,
    fail_on_breaking: bool = True,
    fail_on_dangerous: bool = False,
    max_breaking: int = 0,
    max_dangerous: int = -1,
) -> GateResult:
    """Check if a diff result passes the CI gate.

    Args:
        result: The diff result to check.
        fail_on_breaking: If True, any breaking change fails the gate.
        fail_on_dangerous: If True, any dangerous change fails the gate.
        max_breaking: Maximum allowed breaking changes. -1 means unlimited.
        max_dangerous: Maximum allowed dangerous changes. -1 means unlimited.

    Returns:
        GateResult with pass/fail status and details.
    """
    breaking_count = len(result.breaking_changes)
    dangerous_count = len(result.dangerous_changes)

    # Determine effective thresholds
    if max_breaking >= 0:
        if fail_on_breaking or max_breaking > 0:  # noqa: SIM108
            effective_max_breaking = max_breaking
        else:
            effective_max_breaking = -1 # unlimited
    elif fail_on_breaking:
        effective_max_breaking = 0   # default: zero tolerance
    else:
        effective_max_breaking = -1  # unlimited

    if max_dangerous >= 0:
        if fail_on_dangerous or max_dangerous > 0:  # noqa: SIM108
            effective_max_dangerous = max_dangerous
        else:
            effective_max_dangerous = -1 # unlimited
    elif fail_on_dangerous:
        effective_max_dangerous = 0   # default: zero tolerance
    else:
        effective_max_dangerous = -1  # unlimited

    # Check breaking
    breaking_fails = effective_max_breaking >= 0 and breaking_count > effective_max_breaking

    # Check dangerous
    dangerous_fails = effective_max_dangerous >= 0 and dangerous_count > effective_max_dangerous

    passed = not breaking_fails and not dangerous_fails
    exit_code = 0 if passed else 1

    parts = []
    if breaking_count > 0:
        parts.append(f"{breaking_count} breaking change(s)")
    if dangerous_count > 0:
        parts.append(f"{dangerous_count} dangerous change(s)")

    if passed:
        msg = "CI gate PASSED"
        if parts:
            msg += f" ({', '.join(parts)} detected but allowed)"
    else:
        reasons = []
        if breaking_fails:
            reasons.append("breaking changes exceed threshold")
        if dangerous_fails:
            reasons.append("dangerous changes exceed threshold")
        msg = f"CI gate FAILED: {'; '.join(reasons)}"

    return GateResult(
        passed=passed,
        breaking_count=breaking_count,
        dangerous_count=dangerous_count,
        message=msg,
        exit_code=exit_code,
    )
