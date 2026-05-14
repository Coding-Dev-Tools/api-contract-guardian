"""OpenAPI spec loader and parser."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class SpecLoadError(Exception):
    """Raised when a spec file cannot be loaded or parsed."""


def load_spec(path: str | Path) -> dict[str, Any]:
    """Load an OpenAPI spec from a YAML or JSON file.

    Args:
        path: Path to the spec file.

    Returns:
        Parsed spec as a dict.

    Raises:
        SpecLoadError: If the file cannot be read or parsed.
    """
    path = Path(path)
    if not path.exists():
        raise SpecLoadError(f"Spec file not found: {path}")

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecLoadError(f"Cannot read {path}: {exc}") from exc

    if path.suffix in (".yaml", ".yml"):
        try:
            spec = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise SpecLoadError(f"Invalid YAML in {path}: {exc}") from exc
    elif path.suffix == ".json":
        try:
            spec = json.loads(content)
        except json.JSONDecodeError as exc:
            raise SpecLoadError(f"Invalid JSON in {path}: {exc}") from exc
    else:
        # Try YAML first, then JSON
        try:
            spec = yaml.safe_load(content)
        except yaml.YAMLError:
            try:
                spec = json.loads(content)
            except json.JSONDecodeError as exc:
                raise SpecLoadError(f"Cannot parse {path} as YAML or JSON: {exc}") from exc

    if not isinstance(spec, dict):
        raise SpecLoadError(f"Spec in {path} is not a valid OpenAPI document (expected dict, got {type(spec).__name__})")

    return spec


def load_spec_from_string(content: str, fmt: str = "yaml") -> dict[str, Any]:
    """Load an OpenAPI spec from a string.

    Args:
        content: The spec content as a string.
        fmt: Format hint - 'yaml' or 'json'.

    Returns:
        Parsed spec as a dict.
    """
    if fmt == "json":
        try:
            spec = json.loads(content)
        except json.JSONDecodeError as exc:
            raise SpecLoadError(f"Invalid JSON: {exc}") from exc
        if not isinstance(spec, dict):
            raise SpecLoadError(f"Spec is not a valid OpenAPI document (expected dict, got {type(spec).__name__})")
        return spec
    else:
        try:
            spec = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise SpecLoadError(f"Invalid YAML: {exc}") from exc

        if not isinstance(spec, dict):
            raise SpecLoadError(f"Spec is not a valid OpenAPI document (expected dict, got {type(spec).__name__})")

        return spec


def validate_openapi_version(spec: dict[str, Any]) -> str:
    """Check and return the OpenAPI version of a spec.

    Args:
        spec: Parsed OpenAPI spec.

    Returns:
        Version string (e.g. '3.0.0', '3.1.0').

    Raises:
        SpecLoadError: If the version is not OpenAPI 3.x.
    """
    version = spec.get("openapi", spec.get("swagger", ""))
    if not version:
        raise SpecLoadError("Spec does not contain 'openapi' or 'swagger' version field")

    if version.startswith("3."):
        return version

    if version.startswith("2."):
        raise SpecLoadError(
            f"OpenAPI {version} (Swagger) is not supported. Only OpenAPI 3.x specs are supported."
        )

    raise SpecLoadError(f"Unrecognized OpenAPI version: {version}")


def get_paths(spec: dict[str, Any]) -> dict[str, Any]:
    """Extract paths from a spec."""
    return spec.get("paths", {})


def get_schemas(spec: dict[str, Any]) -> dict[str, Any]:
    """Extract component schemas from a spec."""
    return spec.get("components", {}).get("schemas", {})


def get_operations(path_item: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract HTTP methods (operations) from a path item."""
    methods = {}
    for method in ("get", "post", "put", "patch", "delete", "head", "options", "trace"):
        if method in path_item:
            methods[method] = path_item[method]
    return methods
