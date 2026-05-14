"""CLI entry point for API Contract Guardian."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .diff import DiffResult, Severity, diff_specs
from .gate import GateResult, check_gate
from .loader import SpecLoadError, load_spec, validate_openapi_version
from .migration import generate_migration_guide, generate_migration_guide_json

app = typer.Typer(
    name="api-contract-guardian",
    help="Detect breaking changes in OpenAPI specs and gate CI pipelines.",
    add_completion=False,
)
console = Console()


def _load_and_validate(path: str) -> dict:
    """Load a spec and validate its OpenAPI version."""
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


def _print_result(result: DiffResult) -> None:
    """Print a rich summary of the diff result."""
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
            console.print(f"  [red]-[/red] {c.kind} at [dim]{c.path}[/dim]: {c.description}")

    if result.dangerous_changes:
        console.print("\n[yellow bold]Dangerous Changes:[/yellow bold]")
        for c in result.dangerous_changes:
            console.print(f"  [yellow]-[/yellow] {c.kind} at [dim]{c.path}[/dim]: {c.description}")

    if result.non_breaking_changes:
        console.print("\n[green bold]Non-Breaking Changes:[/green bold]")
        for c in result.non_breaking_changes:
            console.print(f"  [green]+[/green] {c.kind} at [dim]{c.path}[/dim]: {c.description}")

    if result.info_changes:
        console.print("\n[blue bold]Informational:[/blue bold]")
        for c in result.info_changes:
            console.print(f"  [blue]*[/blue] {c.kind} at [dim]{c.path}[/dim]: {c.description}")


@app.command()
def diff(
    old: str = typer.Argument(..., help="Path to old (baseline) OpenAPI spec"),
    new: str = typer.Argument(..., help="Path to new (proposed) OpenAPI spec"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("rich", "--format", "-f", help="Output format: rich, json, markdown"),
) -> None:
    """Compare two OpenAPI specs and show all detected changes."""
    old_spec = _load_and_validate(old)
    new_spec = _load_and_validate(new)

    result = diff_specs(old_spec, new_spec)

    if format == "json":
        output_data = json.dumps(result.to_dict(), indent=2)
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
    fail_on_breaking: bool = typer.Option(True, "--fail-on-breaking/--allow-breaking", help="Fail on breaking changes"),
    fail_on_dangerous: bool = typer.Option(False, "--fail-on-dangerous/--allow-dangerous", help="Fail on dangerous changes"),
    max_breaking: int = typer.Option(0, "--max-breaking", help="Max allowed breaking changes (default 0)"),
    max_dangerous: int = typer.Option(-1, "--max-dangerous", help="Max allowed dangerous changes (-1=unlimited)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Gate CI pipeline on breaking changes. Returns exit code 1 if gate fails."""
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

    if gate_result.passed:
        console.print(f"[green bold]{gate_result.message}[/green bold]")
    else:
        console.print(f"[red bold]{gate_result.message}[/red bold]")

    # Still show the summary
    _print_result(result)

    if output:
        output_data = json.dumps({
            "gate": gate_result.to_dict(),
            "diff": result.to_dict(),
        }, indent=2)
        Path(output).write_text(output_data, encoding="utf-8")
        console.print(f"\nJSON output written to {output}")

    raise typer.Exit(code=gate_result.exit_code)


@app.command()
def migrate(
    old: str = typer.Argument(..., help="Path to old (baseline) OpenAPI spec"),
    new: str = typer.Argument(..., help="Path to new (proposed) OpenAPI spec"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, json"),
) -> None:
    """Generate a migration guide between two OpenAPI spec versions."""
    old_spec = _load_and_validate(old)
    new_spec = _load_and_validate(new)

    result = diff_specs(old_spec, new_spec)

    if format == "json":
        guide = generate_migration_guide_json(result)
        content = json.dumps(guide, indent=2)
    else:
        content = generate_migration_guide(result)

    if output:
        Path(output).write_text(content, encoding="utf-8")
        console.print(f"Migration guide written to {output}")
    else:
        console.print(content)


@app.command()
def version() -> None:
    """Show the version of API Contract Guardian."""
    from . import __version__
    console.print(f"api-contract-guardian v{__version__}")


if __name__ == "__main__":
    app()
