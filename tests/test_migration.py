"""Tests for the migration module."""

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
        changes = [
            Change(kind="path_removed", severity=Severity.BREAKING, path="paths./users", description="Path removed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Breaking Changes" in guide
        assert "path_removed" in guide

    def test_dangerous_changes_section(self):
        changes = [
            Change(
                kind="operation_deprecated", severity=Severity.DANGEROUS, path="paths./old", description="Deprecated"
            )
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Dangerous Changes" in guide

    def test_non_breaking_changes_section(self):
        changes = [
            Change(kind="path_added", severity=Severity.NON_BREAKING, path="paths./new", description="Path added")
        ]
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
        changes = [
            Change(kind="path_removed", severity=Severity.BREAKING, path="paths./users", description="Path removed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Recommended Migration Steps" in guide

    def test_no_migration_steps_without_breaking(self):
        changes = [Change(kind="path_added", severity=Severity.NON_BREAKING, path="paths./new", description="Added")]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Recommended Migration Steps" not in guide

    def test_value_change_shown(self):
        changes = [
            Change(
                kind="type_changed",
                severity=Severity.BREAKING,
                path="x",
                description="Type changed",
                old_value="string",
                new_value="integer",
            )
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Before" in guide
        assert "After" in guide


class TestMigrationStepGeneration:
    """Tests that _generate_steps produces correct steps for each breaking change kind."""

    def test_path_removed_step(self):
        changes = [
            Change(kind="path_removed", severity=Severity.BREAKING, path="paths./users", description="Path removed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Remove client code referencing removed paths" in guide
        assert "paths./users" in guide

    def test_operation_removed_step(self):
        changes = [
            Change(kind="operation_removed", severity=Severity.BREAKING, path="paths./users.delete", description="DELETE removed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "stop calling removed operations" in guide

    def test_parameter_became_required_step(self):
        changes = [
            Change(kind="parameter_became_required", severity=Severity.BREAKING, path="paths./users.get.parameters.query.id", description="Param became required")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Add required parameters to requests" in guide

    def test_required_parameter_added_step(self):
        changes = [
            Change(kind="parameter_added", severity=Severity.BREAKING, path="paths./users.get.parameters.query.sort", description="Parameter 'sort' (query) was added (required)")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Add newly required parameters" in guide

    def test_schema_removed_step(self):
        changes = [
            Change(kind="schema_removed", severity=Severity.BREAKING, path="components.schemas.Legacy", description="Schema removed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Replace removed schemas" in guide
        assert "components.schemas.Legacy" in guide

    def test_type_changed_step(self):
        changes = [
            Change(kind="property_type_changed", severity=Severity.BREAKING, path="components.schemas.User.age", description="Type changed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Update type handling code" in guide

    def test_schema_type_changed_step(self):
        changes = [
            Change(kind="schema_type_changed", severity=Severity.BREAKING, path="components.schemas.User", description="Schema type changed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Update type handling code" in guide

    def test_parameter_type_changed_step(self):
        changes = [
            Change(kind="parameter_type_changed", severity=Severity.BREAKING, path="paths./users.get.parameters.query.id", description="Param type changed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Update type handling code" in guide

    def test_property_removed_step(self):
        changes = [
            Change(kind="property_removed", severity=Severity.BREAKING, path="components.schemas.User.email", description="Property removed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Update code that references removed properties" in guide

    def test_enum_values_removed_step(self):
        changes = [
            Change(kind="enum_values_removed", severity=Severity.BREAKING, path="components.schemas.Status", description="Enum values removed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Update enum value references" in guide

    def test_request_body_became_required_step(self):
        changes = [
            Change(kind="request_body_became_required", severity=Severity.BREAKING, path="paths./users.post.requestBody", description="Request body became required")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "include required request bodies" in guide

    def test_content_type_removed_step(self):
        changes = [
            Change(kind="request_content_type_removed", severity=Severity.BREAKING, path="paths./users.post.requestBody.content.application/xml", description="Content type removed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "content-type handling" in guide

    def test_response_content_type_removed_step(self):
        changes = [
            Change(kind="response_content_type_removed", severity=Severity.BREAKING, path="paths./users.get.responses.200.content.application/xml", description="Response content type removed")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "content-type handling" in guide

    def test_unrecognized_breaking_change_fallback_step(self):
        """An unrecognized breaking change kind still produces a generic step."""
        changes = [
            Change(kind="some_new_breaking_kind", severity=Severity.BREAKING, path="x", description="Unknown")
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Recommended Migration Steps" in guide
        assert "Review breaking changes" in guide

    def test_multiple_step_types_combined(self):
        """Multiple different breaking change kinds produce multiple distinct steps."""
        changes = [
            Change(kind="path_removed", severity=Severity.BREAKING, path="paths./old", description="Path removed"),
            Change(kind="schema_removed", severity=Severity.BREAKING, path="components.schemas.Old", description="Schema removed"),
            Change(kind="enum_values_removed", severity=Severity.BREAKING, path="components.schemas.Status", description="Enum values removed"),
        ]
        result = _make_result(changes=changes)
        guide = generate_migration_guide(result)
        assert "Remove client code referencing removed paths" in guide
        assert "Replace removed schemas" in guide
        assert "Update enum value references" in guide


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
