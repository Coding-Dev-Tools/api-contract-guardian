"""CLI entry point for API Contract Guardian."""

from __future__ import annotations

import typer
from pathlib import Path
from typing import Any

# Lazy imports — jwt+cryptography+deepdiff+yaml add ~200ms at module level.
# Deferring heavy deps to command execution cuts cold start from ~440ms to ~180ms.

try:
    from revenueholdings_license import require_license
    _has_rh = True
except ImportError:
    import warnings
    warnings.warn("revenueholdings-license not installed; license checks skipped", stacklevel=2)
    _has_rh = False
    def require_license(product: str) -> None:  # type: ignore[misc]
        pass


def _require_license(tool_name: str) -> None:
    """Lazily check revenueholdings license only when a command runs."""
    import os
    if os.environ.get("REVENUEHOLDINGS_LICENSE_BYPASS"):
        return
    try:
        from revenueholdings_license import require_license
        require_license(tool_name)
    except ImportError:
        pass


def _validate_output_format(format_name: str, allowed: tuple[str, ...], command: str) -> str:
    """Reject unsupported output formats before the command runs."""
    if format_name not in allowed:
        allowed_list = ", ".join(allowed)
        raise typer.BadParameter(
            f"Unsupported {command} format '{format_name}'. Choose from: {allowed_list}"
        )
    return format_name


app = typer.Typer(
    name="api-contract-guardian",
    help="Detect breaking changes in OpenAPI specs and gate CI pipelines.",
    add_completion=False,
)

_console = None


def _get_console() -> Any:
    global _console
    if _console is None:
        from rich.console import Console
        _console = Console()
    return _console


def _load_and_validate(path: str) -> dict:
    """Load a spec and validate its OpenAPI version."""
    from .loader import SpecLoadError, load_spec, validate_openapi_version
    console = _get_console()
    try:
        spec = load_spec(path)
    except SpecLoadError as exc:
        console.print(f"[red]Error loading {path}:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    try:
        validate_openapi_version(spec)
    except SpecLoadError as exc:
        console.print(f"[red]Error validating {path}:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    return spec


def _print_result(result) -> None:
    """Print a rich summary of the diff result."""
    from rich.table import Table
    console = _get_console()
    summary = result.to_dict()["summary"]

    table = Table(title="Change Summary")
    table.add_column("Severity", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("[red]Breaking[/red]", str(summary["breaking"]))
    table.add_row("[yellow]Dangerous[/yellow]", str(summary["dangerous"]))
    table.add_row("[green]Non-breaking[/green]", str(summary["non_breaking"]))
    table.add_row("[blue]Info[/blue]", str(summary["info"]))
    console.print(table)

    if result.breaking_changes:
        console.print("\n[red bold]Breaking Changes:[/red bold]")
        for c in result.breaking_changes:
            console.print(f" [red]-[/red] {c.kind} at [dim]{c.path}[/dim]: {c.description}")

    if result.dangerous_changes:
        console.print("\n[yellow bold]Dangerous Changes:[/yellow bold]")
        for c in result.dangerous_changes:
            console.print(f" [yellow]-[/yellow] {c.kind} at [dim]{c.path}[/dim]: {c.description}")

    if result.non_breaking_changes:
        console.print("\n[green bold]Non-Breaking Changes:[/green bold]")
        for c in result.non_breaking_changes:
            console.print(f" [green]+[/green] {c.kind} at [dim]{c.path}[/dim]: {c.description}")

    if result.info_changes:
        console.print("\n[blue bold]Informational:[/blue bold]")
        for c in result.info_changes:
            console.print(f" [blue]*[/blue] {c.kind} at [dim]{c.path}[/dim]: {c.description}")


@app.command()
def diff(
    old: str = typer.Argument(..., help="Path to old (baseline) OpenAPI spec"),
    new: str = typer.Argument(..., help="Path to new (proposed) OpenAPI spec"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("rich", "--format", "-f", help="Output format: rich, json, yaml, markdown"),
) -> None:
    """Compare two OpenAPI specs and show all detected changes."""
    import json
    import yaml

    from .diff import diff_specs
    from .migration import generate_migration_guide

    _require_license("api-contract-guardian")
    format = _validate_output_format(format, ("rich", "json", "yaml", "markdown"), "diff")
    old_spec = _load_and_validate(old)
    new_spec = _load_and_validate(new)

    result = diff_specs(old_spec, new_spec)
    console = _get_console()

    if format == "json":
        output_data = json.dumps(result.to_dict(), indent=2)
        if output:
            Path(output).write_text(output_data, encoding="utf-8")
            console.print(f"Written to {output}")
        else:
            console.print(output_data)
    elif format == "yaml":
        output_data = yaml.safe_dump(result.to_dict(), sort_keys=False, default_flow_style=False)
        if output:
            Path(output).write_text(output_data, encoding="utf-8")
            console.print(f"Written to {output}")
        else:
            console.print(output_data)
    elif format == "markdown":
        guide = generate_migration_guide(result)
        if output:
            Path(output).write_text(guide, encoding="utf-8")
            console.print(f"Written to {output}")
        else:
            console.print(guide)
    else:
        _print_result(result)
        if output:
            output_data = json.dumps(result.to_dict(), indent=2)
            Path(output).write_text(output_data, encoding="utf-8")
            console.print(f"\nJSON output written to {output}")


@app.command()
def check(
    old: str = typer.Argument(..., help="Path to old (baseline) OpenAPI spec"),
    new: str = typer.Argument(..., help="Path to new (proposed) OpenAPI spec"),
    fail_on_breaking: bool = typer.Option(
        True, "--fail-on-breaking/--allow-breaking", help="Fail on breaking changes",
    ),
    fail_on_dangerous: bool = typer.Option(
        False, "--fail-on-dangerous/--allow-dangerous", help="Fail on dangerous changes",
    ),
    max_breaking: int = typer.Option(-1, "--max-breaking", help="Max breaking changes (-1=defer, 0=none)"),
    max_dangerous: int = typer.Option(-1, "--max-dangerous", help="Max dangerous changes (-1=defer, 0=none)"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("rich", "--format", "-f", help="Output format: rich, json, yaml"),
) -> None:
    """Gate CI pipeline on breaking changes. Returns exit code 1 if gate fails."""
    import json
    import yaml

    from .diff import diff_specs
    from .gate import check_gate

    _require_license("api-contract-guardian")
    format = _validate_output_format(format, ("rich", "json", "yaml"), "check")
    old_spec = _load_and_validate(old)
    new_spec = _load_and_validate(new)

    result = diff_specs(old_spec, new_spec)
    gate_result = check_gate(
        result,
        fail_on_breaking=fail_on_breaking,
        fail_on_dangerous=fail_on_dangerous,
        max_breaking=max_breaking,
        max_dangerous=max_dangerous,
    )
    console = _get_console()

    if gate_result.passed:
        console.print(f"[green bold]{gate_result.message}[/green bold]")
    else:
        console.print(f"[red bold]{gate_result.message}[/red bold]")

    if format == "rich":
        # Still show the summary for human-friendly output.
        _print_result(result)
    else:
        payload = {
            "gate": gate_result.to_dict(),
            "diff": result.to_dict(),
        }
        if format == "yaml":
            output_data = yaml.safe_dump(payload, sort_keys=False, default_flow_style=False)
        else:
            output_data = json.dumps(payload, indent=2)
        console.print(output_data)

    if output:
        payload = {
            "gate": gate_result.to_dict(),
            "diff": result.to_dict(),
        }
        if format == "yaml":
            output_data = yaml.safe_dump(payload, sort_keys=False, default_flow_style=False)
        else:
            output_data = json.dumps(payload, indent=2)
        Path(output).write_text(output_data, encoding="utf-8")
        console.print(f"\nWritten to {output}")

    raise typer.Exit(code=gate_result.exit_code)


@app.command()
def migrate(
    old: str = typer.Argument(..., help="Path to old (baseline) OpenAPI spec"),
    new: str = typer.Argument(..., help="Path to new (proposed) OpenAPI spec"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, json, yaml"),
) -> None:
    """Generate a migration guide between two OpenAPI spec versions."""
    import json
    import yaml

    from .diff import diff_specs
    from .migration import generate_migration_guide, generate_migration_guide_json

    _require_license("api-contract-guardian")
    format = _validate_output_format(format, ("markdown", "json", "yaml"), "migrate")
    old_spec = _load_and_validate(old)
    new_spec = _load_and_validate(new)

    result = diff_specs(old_spec, new_spec)
    console = _get_console()

    if format == "json":
        guide = generate_migration_guide_json(result)
        content = json.dumps(guide, indent=2)
    elif format == "yaml":
        guide = generate_migration_guide_json(result)
        content = yaml.safe_dump(guide, sort_keys=False, default_flow_style=False)
    else:
        content = generate_migration_guide(result)

    if output:
        Path(output).write_text(content, encoding="utf-8")
        console.print(f"Migration guide written to {output}")
    else:
        console.print(content)


@app.command()
def mcp() -> None:
    """Run as an MCP (Model Context Protocol) server over stdio.

    AI coding agents (Claude Code, Cursor, etc.) use this to interact
    with api-contract-guardian tools directly.
    """
    _require_license("api-contract-guardian")
    from click_to_mcp import run
    run(app)


@app.command()
def version() -> None:
    """Show the version of API Contract Guardian."""
    _require_license("api-contract-guardian")
    from . import __version__
    _get_console().print(f"api-contract-guardian v{__version__}")


if __name__ == "__main__":
    app()
