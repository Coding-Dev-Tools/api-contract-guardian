"""Core diff engine — detect breaking and non-breaking changes between OpenAPI specs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from deepdiff import DeepDiff


class Severity(str, Enum):
    BREAKING = "breaking"
    DANGEROUS = "dangerous"
    NON_BREAKING = "non_breaking"
    INFO = "info"


@dataclass
class Change:
    """A single detected change between two specs."""

    kind: str
    severity: Severity
    path: str
    description: str
    old_value: Any = None
    new_value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "severity": self.severity.value,
            "path": self.path,
            "description": self.description,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass
class DiffResult:
    """Result of comparing two OpenAPI specs."""

    changes: list[Change] = field(default_factory=list)
    old_version: str = ""
    new_version: str = ""

    @property
    def breaking_changes(self) -> list[Change]:
        return [c for c in self.changes if c.severity == Severity.BREAKING]

    @property
    def dangerous_changes(self) -> list[Change]:
        return [c for c in self.changes if c.severity == Severity.DANGEROUS]

    @property
    def non_breaking_changes(self) -> list[Change]:
        return [c for c in self.changes if c.severity == Severity.NON_BREAKING]

    @property
    def info_changes(self) -> list[Change]:
        return [c for c in self.changes if c.severity == Severity.INFO]

    @property
    def has_breaking(self) -> bool:
        return len(self.breaking_changes) > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "old_version": self.old_version,
            "new_version": self.new_version,
            "summary": {
                "breaking": len(self.breaking_changes),
                "dangerous": len(self.dangerous_changes),
                "non_breaking": len(self.non_breaking_changes),
                "info": len(self.info_changes),
            },
            "changes": [c.to_dict() for c in self.changes],
        }


def diff_specs(old: dict[str, Any], new: dict[str, Any]) -> DiffResult:
    """Compare two OpenAPI specs and return all detected changes.

    Args:
        old: The old (baseline) OpenAPI spec.
        new: The new (proposed) OpenAPI spec.

    Returns:
        DiffResult with all detected changes classified by severity.
    """
    result = DiffResult()

    old_version = old.get("openapi", old.get("swagger", "unknown"))
    new_version = new.get("openapi", new.get("swagger", "unknown"))
    result.old_version = old_version
    result.new_version = new_version

    # Check paths
    _diff_paths(old, new, result)

    # Check schemas/components
    _diff_schemas(old, new, result)

    # Check security schemes
    _diff_security_schemes(old, new, result)

    # Check global security requirements
    _diff_security_requirements(old, new, result)

    # Check server configurations
    _diff_servers(old, new, result)

    # Check info metadata
    _diff_info(old, new, result)

    return result


def _diff_paths(old: dict[str, Any], new: dict[str, Any], result: DiffResult) -> None:
    """Detect changes in paths and operations."""
    old_paths = old.get("paths", {})
    new_paths = new.get("paths", {})

    # Removed paths — BREAKING
    for path in old_paths:
        if path not in new_paths:
            result.changes.append(Change(
                kind="path_removed",
                severity=Severity.BREAKING,
                path=f"paths.{path}",
                description=f"Path '{path}' was removed",
                old_value=path,
                new_value=None,
            ))

    # Added paths — NON_BREAKING
    for path in new_paths:
        if path not in old_paths:
            result.changes.append(Change(
                kind="path_added",
                severity=Severity.NON_BREAKING,
                path=f"paths.{path}",
                description=f"Path '{path}' was added",
                old_value=None,
                new_value=path,
            ))

    # Check operations within shared paths
    for path in old_paths:
        if path not in new_paths:
            continue
        _diff_operations(path, old_paths[path], new_paths[path], result)


def _diff_operations(
    path: str,
    old_item: dict[str, Any],
    new_item: dict[str, Any],
    result: DiffResult,
) -> None:
    """Detect changes in operations within a shared path."""
    methods = ("get", "post", "put", "patch", "delete", "head", "options", "trace")

    for method in methods:
        old_op = old_item.get(method)
        new_op = new_item.get(method)

        if old_op and not new_op:
            result.changes.append(Change(
                kind="operation_removed",
                severity=Severity.BREAKING,
                path=f"paths.{path}.{method}",
                description=f"{method.upper()} {path} was removed",
                old_value=method,
                new_value=None,
            ))
        elif not old_op and new_op:
            result.changes.append(Change(
                kind="operation_added",
                severity=Severity.NON_BREAKING,
                path=f"paths.{path}.{method}",
                description=f"{method.upper()} {path} was added",
                old_value=None,
                new_value=method,
            ))
        elif old_op and new_op:
            _diff_operation_details(path, method, old_op, new_op, result)


def _diff_operation_details(
    path: str,
    method: str,
    old_op: dict[str, Any],
    new_op: dict[str, Any],
    result: DiffResult,
) -> None:
    """Detect changes within an operation (parameters, responses, requestBody)."""
    op_path = f"paths.{path}.{method}"

    # Check parameters
    _diff_parameters(op_path, old_op.get("parameters", []), new_op.get("parameters", []), result)

    # Check request body
    _diff_request_body(op_path, old_op.get("requestBody"), new_op.get("requestBody"), result)

    # Check responses
    _diff_responses(op_path, old_op.get("responses", {}), new_op.get("responses", {}), result)

    # Check if operation became deprecated
    if not old_op.get("deprecated") and new_op.get("deprecated"):
        result.changes.append(Change(
            kind="operation_deprecated",
            severity=Severity.DANGEROUS,
            path=op_path,
            description=f"{method.upper()} {path} is now deprecated",
        ))

    # Check if operation became required (new required param)
    # Handled in _diff_parameters


def _diff_parameters(
    op_path: str,
    old_params: list[dict[str, Any]],
    new_params: list[dict[str, Any]],
    result: DiffResult,
) -> None:
    """Detect parameter changes."""
    old_by_key = {}
    for p in old_params:
        key = (p.get("in", ""), p.get("name", ""))
        old_by_key[key] = p

    new_by_key = {}
    for p in new_params:
        key = (p.get("in", ""), p.get("name", ""))
        new_by_key[key] = p

    # Removed parameters
    for key, param in old_by_key.items():
        if key not in new_by_key:
            result.changes.append(Change(
                kind="parameter_removed",
                severity=Severity.BREAKING if param.get("required", False) else Severity.NON_BREAKING,
                path=f"{op_path}.parameters.{key[0]}.{key[1]}",
                description=f"Parameter '{key[1]}' ({key[0]}) was removed",
                old_value=param,
                new_value=None,
            ))

    # Added parameters
    for key, param in new_by_key.items():
        if key not in old_by_key:
            sev = Severity.BREAKING if param.get("required", False) else Severity.NON_BREAKING
            result.changes.append(Change(
                kind="parameter_added",
                severity=sev,
                path=f"{op_path}.parameters.{key[0]}.{key[1]}",
                description=f"Parameter '{key[1]}' ({key[0]}) was added" + (" (required)" if param.get("required") else ""),
                old_value=None,
                new_value=param,
            ))

    # Changed parameters
    for key in old_by_key:
        if key not in new_by_key:
            continue
        old_p = old_by_key[key]
        new_p = new_by_key[key]

        # Required flag changed
        if not old_p.get("required", False) and new_p.get("required", False):
            result.changes.append(Change(
                kind="parameter_became_required",
                severity=Severity.BREAKING,
                path=f"{op_path}.parameters.{key[0]}.{key[1]}",
                description=f"Parameter '{key[1]}' ({key[0]}) became required",
            ))

        # Type changed
        if old_p.get("schema", {}).get("type") != new_p.get("schema", {}).get("type"):
            old_type = old_p.get("schema", {}).get("type")
            new_type = new_p.get("schema", {}).get("type")
            if old_type and new_type:
                result.changes.append(Change(
                    kind="parameter_type_changed",
                    severity=Severity.BREAKING,
                    path=f"{op_path}.parameters.{key[0]}.{key[1]}",
                    description=f"Parameter '{key[1]}' type changed from '{old_type}' to '{new_type}'",
                    old_value=old_type,
                    new_value=new_type,
                ))


def _diff_request_body(
    op_path: str,
    old_rb: dict[str, Any] | None,
    new_rb: dict[str, Any] | None,
    result: DiffResult,
) -> None:
    """Detect request body changes."""
    rb_path = f"{op_path}.requestBody"

    if old_rb and not new_rb:
        result.changes.append(Change(
            kind="request_body_removed",
            severity=Severity.BREAKING,
            path=rb_path,
            description="Request body was removed",
        ))
        return

    if not old_rb and new_rb:
        result.changes.append(Change(
            kind="request_body_added",
            severity=Severity.NON_BREAKING,
            path=rb_path,
            description="Request body was added",
        ))
        return

    if not old_rb or not new_rb:
        return

    # Required flag changed
    if not old_rb.get("required", False) and new_rb.get("required", False):
        result.changes.append(Change(
            kind="request_body_became_required",
            severity=Severity.BREAKING,
            path=rb_path,
            description="Request body became required",
        ))

    # Content type changes
    old_content = old_rb.get("content", {})
    new_content = new_rb.get("content", {})

    for ct in old_content:
        if ct not in new_content:
            result.changes.append(Change(
                kind="request_content_type_removed",
                severity=Severity.BREAKING,
                path=f"{rb_path}.content.{ct}",
                description=f"Request content type '{ct}' was removed",
            ))

    for ct in new_content:
        if ct not in old_content:
            result.changes.append(Change(
                kind="request_content_type_added",
                severity=Severity.NON_BREAKING,
                path=f"{rb_path}.content.{ct}",
                description=f"Request content type '{ct}' was added",
            ))


def _diff_responses(
    op_path: str,
    old_resp: dict[str, Any],
    new_resp: dict[str, Any],
    result: DiffResult,
) -> None:
    """Detect response changes."""
    resp_path = f"{op_path}.responses"

    for code in old_resp:
        if code not in new_resp:
            result.changes.append(Change(
                kind="response_removed",
                severity=Severity.BREAKING,
                path=f"{resp_path}.{code}",
                description=f"Response '{code}' was removed",
            ))

    for code in new_resp:
        if code not in old_resp:
            result.changes.append(Change(
                kind="response_added",
                severity=Severity.NON_BREAKING,
                path=f"{resp_path}.{code}",
                description=f"Response '{code}' was added",
            ))

    for code in old_resp:
        if code not in new_resp:
            continue
        old_content = old_resp[code].get("content", {})
        new_content = new_resp[code].get("content", {})

        for ct in old_content:
            if ct not in new_content:
                result.changes.append(Change(
                    kind="response_content_type_removed",
                    severity=Severity.BREAKING,
                    path=f"{resp_path}.{code}.content.{ct}",
                    description=f"Response content type '{ct}' for '{code}' was removed",
                ))

        for ct in new_content:
            if ct not in old_content:
                result.changes.append(Change(
                    kind="response_content_type_added",
                    severity=Severity.NON_BREAKING,
                    path=f"{resp_path}.{code}.content.{ct}",
                    description=f"Response content type '{ct}' for '{code}' was added",
                ))


def _diff_schemas(old: dict[str, Any], new: dict[str, Any], result: DiffResult) -> None:
    """Detect schema/component changes."""
    old_schemas = old.get("components", {}).get("schemas", {})
    new_schemas = new.get("components", {}).get("schemas", {})

    for name in old_schemas:
        if name not in new_schemas:
            result.changes.append(Change(
                kind="schema_removed",
                severity=Severity.BREAKING,
                path=f"components.schemas.{name}",
                description=f"Schema '{name}' was removed",
            ))

    for name in new_schemas:
        if name not in old_schemas:
            result.changes.append(Change(
                kind="schema_added",
                severity=Severity.NON_BREAKING,
                path=f"components.schemas.{name}",
                description=f"Schema '{name}' was added",
            ))

    for name in old_schemas:
        if name not in new_schemas:
            continue
        _diff_schema_details(name, old_schemas[name], new_schemas[name], result)


def _diff_schema_details(
    name: str,
    old_schema: dict[str, Any],
    new_schema: dict[str, Any],
    result: DiffResult,
) -> None:
    """Detect changes within a schema."""
    schema_path = f"components.schemas.{name}"

    # Type change
    old_type = old_schema.get("type")
    new_type = new_schema.get("type")
    if old_type and new_type and old_type != new_type:
        result.changes.append(Change(
            kind="schema_type_changed",
            severity=Severity.BREAKING,
            path=schema_path,
            description=f"Schema '{name}' type changed from '{old_type}' to '{new_type}'",
            old_value=old_type,
            new_value=new_type,
        ))

    # Required properties changes
    old_required = set(old_schema.get("required", []))
    new_required = set(new_schema.get("required", []))

    newly_required = new_required - old_required
    for prop in newly_required:
        result.changes.append(Change(
            kind="property_became_required",
            severity=Severity.BREAKING,
            path=f"{schema_path}.{prop}",
            description=f"Property '{prop}' in schema '{name}' became required",
        ))

    no_longer_required = old_required - new_required
    for prop in no_longer_required:
        result.changes.append(Change(
            kind="property_no_longer_required",
            severity=Severity.NON_BREAKING,
            path=f"{schema_path}.{prop}",
            description=f"Property '{prop}' in schema '{name}' is no longer required",
        ))

    # Schema-level enum changes (must be outside property loop)
    old_schema_enum = old_schema.get("enum")
    new_schema_enum = new_schema.get("enum")
    if old_schema_enum and new_schema_enum:
        removed_values = set(old_schema_enum) - set(new_schema_enum)
        if removed_values:
            result.changes.append(Change(
                kind="enum_values_removed",
                severity=Severity.BREAKING,
                path=schema_path,
                description=f"Schema '{name}' removed enum values: {removed_values}",
                old_value=list(removed_values),
            ))

    # Property changes
    old_props = old_schema.get("properties", {})
    new_props = new_schema.get("properties", {})

    for prop_name in old_props:
        if prop_name not in new_props:
            result.changes.append(Change(
                kind="property_removed",
                severity=Severity.BREAKING if prop_name in old_required else Severity.DANGEROUS,
                path=f"{schema_path}.properties.{prop_name}",
                description=f"Property '{prop_name}' removed from schema '{name}'",
            ))

    for prop_name in new_props:
        if prop_name not in old_props:
            result.changes.append(Change(
                kind="property_added",
                severity=Severity.NON_BREAKING,
                path=f"{schema_path}.properties.{prop_name}",
                description=f"Property '{prop_name}' added to schema '{name}'",
            ))

    for prop_name in old_props:
        if prop_name not in new_props:
            continue
        old_prop = old_props[prop_name]
        new_prop = new_props[prop_name]

        # Property type change
        if old_prop.get("type") and new_prop.get("type") and old_prop["type"] != new_prop["type"]:
            result.changes.append(Change(
                kind="property_type_changed",
                severity=Severity.BREAKING,
                path=f"{schema_path}.properties.{prop_name}",
                description=f"Property '{prop_name}' in '{name}' type changed from '{old_prop['type']}' to '{new_prop['type']}'",
                old_value=old_prop["type"],
                new_value=new_prop["type"],
            ))

        # Format change
        if old_prop.get("format") != new_prop.get("format"):
            old_fmt = old_prop.get("format", "")
            new_fmt = new_prop.get("format", "")
            if old_fmt and new_fmt and old_fmt != new_fmt:
                result.changes.append(Change(
                    kind="property_format_changed",
                    severity=Severity.DANGEROUS,
                    path=f"{schema_path}.properties.{prop_name}",
                    description=f"Property '{prop_name}' in '{name}' format changed from '{old_fmt}' to '{new_fmt}'",
                    old_value=old_fmt,
                    new_value=new_fmt,
                ))

        # Enum changes
        old_enum = old_prop.get("enum")
        new_enum = new_prop.get("enum")
        if old_enum and new_enum:
            removed_values = set(old_enum) - set(new_enum)
            if removed_values:
                result.changes.append(Change(
                    kind="enum_values_removed",
                    severity=Severity.BREAKING,
                    path=f"{schema_path}.properties.{prop_name}",
                    description=f"Enum property '{prop_name}' in '{name}' removed values: {removed_values}",
                    old_value=list(removed_values),
                ))


def _diff_security_schemes(
    old: dict[str, Any], new: dict[str, Any], result: DiffResult,
) -> None:
    """Detect security scheme changes."""
    old_schemes = old.get("components", {}).get("securitySchemes", {})
    new_schemes = new.get("components", {}).get("securitySchemes", {})

    for name in old_schemes:
        if name not in new_schemes:
            result.changes.append(Change(
                kind="security_scheme_removed",
                severity=Severity.BREAKING,
                path=f"components.securitySchemes.{name}",
                description=f"Security scheme '{name}' was removed",
            ))

    for name in new_schemes:
        if name not in old_schemes:
            result.changes.append(Change(
                kind="security_scheme_added",
                severity=Severity.NON_BREAKING,
                path=f"components.securitySchemes.{name}",
                description=f"Security scheme '{name}' was added",
            ))

    for name in old_schemes:
        if name not in new_schemes:
            continue
        if old_schemes[name].get("type") != new_schemes[name].get("type"):
            result.changes.append(Change(
                kind="security_scheme_type_changed",
                severity=Severity.BREAKING,
                path=f"components.securitySchemes.{name}",
                description=f"Security scheme '{name}' type changed",
                old_value=old_schemes[name].get("type"),
                new_value=new_schemes[name].get("type"),
            ))


def _diff_security_requirements(
    old: dict[str, Any], new: dict[str, Any], result: DiffResult,
) -> None:
    """Detect global security requirement changes."""
    old_sec = old.get("security", [])
    new_sec = new.get("security", [])

    if old_sec and not new_sec:
        result.changes.append(Change(
            kind="global_security_removed",
            severity=Severity.DANGEROUS,
            path="security",
            description="Global security requirements were removed",
        ))
    elif not old_sec and new_sec:
        result.changes.append(Change(
            kind="global_security_added",
            severity=Severity.DANGEROUS,
            path="security",
            description="Global security requirements were added",
        ))


def _diff_servers(old: dict[str, Any], new: dict[str, Any], result: DiffResult) -> None:
    """Detect server configuration changes."""
    old_servers = old.get("servers", [])
    new_servers = new.get("servers", [])

    old_urls = [s.get("url", "") for s in old_servers]
    new_urls = [s.get("url", "") for s in new_servers]

    for url in old_urls:
        if url not in new_urls:
            result.changes.append(Change(
                kind="server_removed",
                severity=Severity.DANGEROUS,
                path=f"servers.{url}",
                description=f"Server '{url}' was removed",
            ))

    for url in new_urls:
        if url not in old_urls:
            result.changes.append(Change(
                kind="server_added",
                severity=Severity.INFO,
                path=f"servers.{url}",
                description=f"Server '{url}' was added",
            ))


def _diff_info(old: dict[str, Any], new: dict[str, Any], result: DiffResult) -> None:
    """Detect info section changes."""
    old_info = old.get("info", {})
    new_info = new.get("info", {})

    old_title = old_info.get("title", "")
    new_title = new_info.get("title", "")

    if old_title != new_title:
        result.changes.append(Change(
            kind="title_changed",
            severity=Severity.INFO,
            path="info.title",
            description=f"API title changed from '{old_title}' to '{new_title}'",
            old_value=old_title,
            new_value=new_title,
        ))

    old_api_version = old_info.get("version", "")
    new_api_version = new_info.get("version", "")

    if old_api_version != new_api_version:
        result.changes.append(Change(
            kind="api_version_changed",
            severity=Severity.INFO,
            path="info.version",
            description=f"API version changed from '{old_api_version}' to '{new_api_version}'",
            old_value=old_api_version,
            new_value=new_api_version,
        ))
