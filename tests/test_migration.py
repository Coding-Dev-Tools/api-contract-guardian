"""Tests for the migration module."""

import pytest

from api_contract_guardian.diff import Change, DiffResult, Severity
from api_contract_guardian.migration import generate_migration_guide, generate_migration_guide_json


def _make_result(changes=None, old_version="3.0.0", new_version="3.1.0"):
    return DiffResult(changes=changes or [], old_version=old_version, new_version=new_version)


class TestGenerateMigrationGuide:
    def test_empty_changes(self):
        result = _make_result()
        guide = generate_migration_guide(result)
        assert "No changes detected" in guide

    def test_has_title(self):
        result = _make_result()
        guide = generate_migration_guide(result)
        assert "# API Migration Guide" in guide

    def test_shows_versions(self):
        result = _make_result(old_version="3.0.0", new_version="3.1.0")
        guide = generate_migration_guide(result)
        assert "3.0.0" in guide
        assert "3.1.0" in guide

    def test_breaking_changes_section(self):
        changes = [Change(kind="path_removed", severity=Severity.BREAKING, path="paths./users", description="Path removed")]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Breaking Changes" in guide
        assert "path_removed" in guide

    def test_dangerous_changes_section(self):
        changes = [Change(kind="operation_deprecated", severity=Severity.DANGEROUS, path="paths./old", description="Deprecated")]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Dangerous Changes" in guide

    def test_non_breaking_changes_section(self):
        changes = [Change(kind="path_added", severity=Severity.NON_BREAKING, path="paths./new", description="Path added")]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Non-Breaking Changes" in guide

    def test_info_section(self):
        changes = [Change(kind="title_changed", severity=Severity.INFO, path="info.title", description="Title changed")]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Informational" in guide

    def test_summary_table(self):
        changes = [
            Change(kind="a", severity=Severity.BREAKING, path="", description=""),
            Change(kind="b", severity=Severity.NON_BREAKING, path="", description=""),
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "| Breaking | 1 |" in guide
        assert "| Non-breaking | 1 |" in guide

    def test_migration_steps_generated_for_breaking(self):
        changes = [Change(kind="path_removed", severity=Severity.BREAKING, path="paths./users", description="Path removed")]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Recommended Migration Steps" in guide

    def test_no_migration_steps_without_breaking(self):
        changes = [Change(kind="path_added", severity=Severity.NON_BREAKING, path="paths./new", description="Added")]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Recommended Migration Steps" not in guide

    def test_value_change_shown(self):
        changes = [Change(kind="type_changed", severity=Severity.BREAKING, path="x", description="Type changed", old_value="string", new_value="integer")]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Before" in guide
        assert "After" in guide


class TestGenerateMigrationGuideJson:
    def test_empty_changes(self):
        result = _make_result()
        guide = generate_migration_guide_json(result)
        assert guide["from_version"] == "3.0.0"
        assert guide["to_version"] == "3.1.0"
        assert guide["breaking_changes"] == []
        assert guide["migration_steps"] == []

    def test_has_breaking_changes(self):
        changes = [Change(kind="path_removed", severity=Severity.BREAKING, path="p", description="d")]
        result = _make_result(changes=changes)
        guide = generate_migration_guide_json(result)
        assert len(guide["breaking_changes"]) == 1
        assert len(guide["migration_steps"]) > 0

    def test_summary_counts(self):
        changes = [
            Change(kind="a", severity=Severity.BREAKING, path="", description=""),
            Change(kind="b", severity=Severity.BREAKING, path="", description=""),
            Change(kind="c", severity=Severity.DANGEROUS, path="", description=""),
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide_json(result)
        assert guide["summary"]["breaking"] == 2
        assert guide["summary"]["dangerous"] == 1
