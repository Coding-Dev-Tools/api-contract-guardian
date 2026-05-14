"""Tests for the gate module."""

import pytest

from api_contract_guardian.diff import Change, DiffResult, Severity
from api_contract_guardian.gate import GateResult, check_gate


def _make_result(breaking=0, dangerous=0, non_breaking=0, info=0):
    """Helper to create a DiffResult with specified change counts."""
    changes = []
    for _ in range(breaking):
        changes.append(Change(kind="x", severity=Severity.BREAKING, path="", description=""))
    for _ in range(dangerous):
        changes.append(Change(kind="x", severity=Severity.DANGEROUS, path="", description=""))
    for _ in range(non_breaking):
        changes.append(Change(kind="x", severity=Severity.NON_BREAKING, path="", description=""))
    for _ in range(info):
        changes.append(Change(kind="x", severity=Severity.INFO, path="", description=""))
    return DiffResult(changes=changes)


class TestGateResult:
    def test_to_dict(self):
        gr = GateResult(passed=True, breaking_count=0, dangerous_count=0, message="OK")
        d = gr.to_dict()
        assert d["passed"] is True
        assert d["breaking_count"] == 0
        assert d["exit_code"] == 0


class TestCheckGate:
    def test_no_changes_passes(self):
        result = _make_result()
        gate = check_gate(result)
        assert gate.passed
        assert gate.exit_code == 0

    def test_breaking_fails_by_default(self):
        result = _make_result(breaking=1)
        gate = check_gate(result)
        assert not gate.passed
        assert gate.exit_code == 1

    def test_dangerous_passes_by_default(self):
        result = _make_result(dangerous=1)
        gate = check_gate(result)
        assert gate.passed

    def test_dangerous_fails_when_configured(self):
        result = _make_result(dangerous=1)
        gate = check_gate(result, fail_on_dangerous=True)
        assert not gate.passed

    def test_non_breaking_always_passes(self):
        result = _make_result(non_breaking=5)
        gate = check_gate(result)
        assert gate.passed

    def test_info_always_passes(self):
        result = _make_result(info=5)
        gate = check_gate(result)
        assert gate.passed

    def test_allow_breaking_with_flag(self):
        result = _make_result(breaking=2)
        gate = check_gate(result, fail_on_breaking=False)
        assert gate.passed

    def test_max_breaking_within_limit(self):
        result = _make_result(breaking=2)
        gate = check_gate(result, max_breaking=2)
        assert gate.passed

    def test_max_breaking_exceeds_limit(self):
        result = _make_result(breaking=3)
        gate = check_gate(result, max_breaking=2)
        assert not gate.passed

    def test_max_dangerous_within_limit(self):
        result = _make_result(dangerous=2)
        gate = check_gate(result, fail_on_breaking=False, max_dangerous=2)
        assert gate.passed

    def test_max_dangerous_exceeds_limit(self):
        result = _make_result(dangerous=3)
        gate = check_gate(result, fail_on_breaking=False, max_dangerous=2)
        assert not gate.passed

    def test_max_breaking_negative_one_unlimited(self):
        result = _make_result(breaking=100)
        gate = check_gate(result, fail_on_breaking=False, max_breaking=-1)
        assert gate.passed

    def test_mixed_changes_breaking_dominates(self):
        result = _make_result(breaking=1, non_breaking=5, info=3)
        gate = check_gate(result)
        assert not gate.passed
        assert gate.breaking_count == 1

    def test_mixed_changes_no_breaking_with_dangerous(self):
        result = _make_result(dangerous=1, non_breaking=5)
        gate = check_gate(result)
        assert gate.passed

    def test_message_on_pass(self):
        result = _make_result()
        gate = check_gate(result)
        assert "PASSED" in gate.message

    def test_message_on_fail(self):
        result = _make_result(breaking=1)
        gate = check_gate(result)
        assert "FAILED" in gate.message

    def test_both_breaking_and_dangerous_fail(self):
        result = _make_result(breaking=1, dangerous=1)
        gate = check_gate(result, fail_on_dangerous=True)
        assert not gate.passed

    def test_zero_max_breaking_with_zero_changes(self):
        result = _make_result(breaking=0)
        gate = check_gate(result, max_breaking=0)
        assert gate.passed

    def test_fail_on_breaking_false_max_breaking_exceeded(self):
        result = _make_result(breaking=3)
        gate = check_gate(result, fail_on_breaking=False, max_breaking=1)
        assert not gate.passed
