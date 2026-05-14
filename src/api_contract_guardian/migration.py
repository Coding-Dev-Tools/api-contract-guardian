"""Migration guide generator — produce human-readable migration guides from diff results."""

from __future__ import annotations

from typing import Any

from .diff import Change, DiffResult, Severity


def generate_migration_guide(result: DiffResult) -> str:
    """Generate a markdown migration guide from diff results.

    Args:
        result: The diff result to generate a guide from.

    Returns:
        Markdown-formatted migration guide string.
    """
    lines: list[str] = []

    lines.append("# API Migration Guide")
    lines.append("")
    lines.append(f"From version `{result.old_version}` to `{result.new_version}`")
    lines.append("")

    # Summary
    summary = result.to_dict()["summary"]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Severity | Count |")
    lines.append(f"|----------|-------|")
    lines.append(f"| Breaking | {summary['breaking']} |")
    lines.append(f"| Dangerous | {summary['dangerous']} |")
    lines.append(f"| Non-breaking | {summary['non_breaking']} |")
    lines.append(f"| Info | {summary['info']} |")
    lines.append("")

    if not result.changes:
        lines.append("No changes detected between specs.")
        return "\n".join(lines)

    # Breaking changes section
    breaking = result.breaking_changes
    if breaking:
        lines.append("## Breaking Changes")
        lines.append("")
        lines.append("These changes **will** break existing clients. Action required.")
        lines.append("")
        for change in breaking:
            lines.append(f"- **{change.kind}** at `{change.path}`: {change.description}")
            if change.old_value is not None or change.new_value is not None:
                lines.append(_format_value_change(change))
        lines.append("")

    # Dangerous changes section
    dangerous = result.dangerous_changes
    if dangerous:
        lines.append("## Dangerous Changes")
        lines.append("")
        lines.append("These changes **may** break existing clients. Review recommended.")
        lines.append("")
        for change in dangerous:
            lines.append(f"- **{change.kind}** at `{change.path}`: {change.description}")
        lines.append("")

    # Non-breaking changes section
    non_breaking = result.non_breaking_changes
    if non_breaking:
        lines.append("## Non-Breaking Changes")
        lines.append("")
        lines.append("These changes are backward-compatible. No action required.")
        lines.append("")
        for change in non_breaking:
            lines.append(f"- **{change.kind}** at `{change.path}`: {change.description}")
        lines.append("")

    # Info section
    info = result.info_changes
    if info:
        lines.append("## Informational")
        lines.append("")
        for change in info:
            lines.append(f"- **{change.kind}** at `{change.path}`: {change.description}")
        lines.append("")

    # Migration steps
    if breaking:
        lines.append("## Recommended Migration Steps")
        lines.append("")
        steps = _generate_steps(breaking)
        for i, step in enumerate(steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")

    return "\n".join(lines)


def _format_value_change(change: Change) -> str:
    """Format a value change for display."""
    parts = []
    if change.old_value is not None:
        parts.append(f"  - Before: `{change.old_value}`")
    if change.new_value is not None:
        parts.append(f"  - After: `{change.new_value}`")
    return "\n".join(parts)


def _generate_steps(breaking_changes: list[Change]) -> list[str]:
    """Generate recommended migration steps from breaking changes."""
    steps = []

    removed_paths = [c for c in breaking_changes if c.kind == "path_removed"]
    if removed_paths:
        paths = ", ".join(f"`{c.path}`" for c in removed_paths)
        steps.append(f"Remove client code referencing removed paths: {paths}")

    removed_ops = [c for c in breaking_changes if c.kind == "operation_removed"]
    if removed_ops:
        ops = ", ".join(f"`{c.path}`" for c in removed_ops)
        steps.append(f"Update client code to stop calling removed operations: {ops}")

    newly_required = [c for c in breaking_changes if c.kind == "parameter_became_required"]
    if newly_required:
        params = ", ".join(f"`{c.path}`" for c in newly_required)
        steps.append(f"Add required parameters to requests: {params}")

    required_params_added = [c for c in breaking_changes if c.kind == "parameter_added" and "(required)" in c.description]
    if required_params_added:
        params = ", ".join(f"`{c.path}`" for c in required_params_added)
        steps.append(f"Add newly required parameters: {params}")

    required_rb = [c for c in breaking_changes if c.kind == "request_body_became_required"]
    if required_rb:
        steps.append("Update requests to include required request bodies")

    removed_schemas = [c for c in breaking_changes if c.kind == "schema_removed"]
    if removed_schemas:
        schemas = ", ".join(f"`{c.path}`" for c in removed_schemas)
        steps.append(f"Replace removed schemas: {schemas}")

    type_changes = [c for c in breaking_changes if c.kind in ("schema_type_changed", "property_type_changed", "parameter_type_changed")]
    if type_changes:
        steps.append("Update type handling code for changed types")

    removed_props = [c for c in breaking_changes if c.kind == "property_removed"]
    if removed_props:
        steps.append("Update code that references removed properties")

    enum_removals = [c for c in breaking_changes if c.kind == "enum_values_removed"]
    if enum_removals:
        steps.append("Update enum value references to remove deleted values")

    removed_content_types = [c for c in breaking_changes if c.kind in ("request_content_type_removed", "response_content_type_removed")]
    if removed_content_types:
        steps.append("Update content-type handling for removed content types")

    if not steps:
        steps.append("Review breaking changes and update client code accordingly")

    return steps


def generate_migration_guide_json(result: DiffResult) -> dict[str, Any]:
    """Generate a structured JSON migration guide from diff results.

    Args:
        result: The diff result to generate a guide from.

    Returns:
        Dictionary with migration guide data.
    """
    guide: dict[str, Any] = {
        "from_version": result.old_version,
        "to_version": result.new_version,
        "summary": result.to_dict()["summary"],
        "breaking_changes": [c.to_dict() for c in result.breaking_changes],
        "dangerous_changes": [c.to_dict() for c in result.dangerous_changes],
        "migration_steps": _generate_steps(result.breaking_changes) if result.breaking_changes else [],
    }
    return guide
