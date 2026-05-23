"""Tests for the CLI interface using Typer's CliRunner."""

from __future__ import annotations

import os
import tempfile
import yaml
from api_contract_guardian.cli import app
from typer.testing import CliRunner

runner = CliRunner()


# ── Helper ──


def _write_yaml(data: dict) -> str:
    """Write a YAML file and return its path."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        return f.name


# ── Fixtures ──


def _identical_specs():
    """Return two identical minimal specs."""
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "List users"}}},
            },
        },
    }
    return _write_yaml(spec), _write_yaml(spec)


def _breaking_specs():
    """Return two specs where an endpoint is removed (breaking change)."""
    old = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "List users"}}},
            },
            "/users/{id}": {
                "delete": {"responses": {"204": {"description": "Deleted"}}},
            },
        },
    }
    new = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "List users"}}},
            },
        },
    }
    return _write_yaml(old), _write_yaml(new)


def _dangerous_specs():
    """Return two specs where an operation is deprecated (dangerous change)."""
    old = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "List users"}}},
            },
        },
    }
    new = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"deprecated": True, "responses": {"200": {"description": "List users"}}},
            },
        },
    }
    return _write_yaml(old), _write_yaml(new)


def _nonbreaking_info_specs():
    """Return two specs producing non-breaking (new path) + info (new server) changes."""
    old = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "List users"}}},
            },
        },
    }
    new = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "List users"}}},
            },
            "/posts": {
                "get": {"responses": {"200": {"description": "List posts"}}},
            },
        },
        "servers": [{"url": "https://api.example.com/v2"}],
    }
    return _write_yaml(old), _write_yaml(new)


class TestVersionCommand:
    """Tests for the ``version`` subcommand."""

    def test_version_output(self):
        """version prints the package version string."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "api-contract-guardian v0.1.0" in result.output

    def test_version_exit_code(self):
        """version exits with code 0."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0


class TestDiffCommand:
    """Tests for the ``diff`` subcommand."""

    def test_diff_json_format(self):
        """diff --format json outputs valid JSON with no changes."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--format", "json"])
            assert result.exit_code == 0
            assert '"breaking": 0' in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_diff_with_breaking_changes_json(self):
        """diff detects breaking changes."""
        old_path, new_path = _breaking_specs()
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--format", "json"])
            assert result.exit_code == 0
            assert '"breaking": 1' in result.output or "path_removed" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_diff_rich_format(self):
        """diff default (rich) format prints a summary table."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["diff", old_path, new_path])
            assert result.exit_code == 0
            assert "Change Summary" in result.output
            assert "Breaking" in result.output
            assert "0" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_diff_output_file(self):
        """diff --output writes JSON to a file."""
        old_path, new_path = _identical_specs()
        out_path = tempfile.mktemp(suffix=".json")
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            assert "summary" in content
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)

    def test_diff_rich_all_categories(self):
        """diff default (rich) format shows non-breaking and info sections when present."""
        old_path, new_path = _nonbreaking_info_specs()
        try:
            result = runner.invoke(app, ["diff", old_path, new_path])
            assert result.exit_code == 0
            assert "Change Summary" in result.output
            assert "Non-Breaking Changes" in result.output
            assert "path_added" in result.output
            assert "Informational" in result.output
            assert "server_added" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_diff_invalid_file(self):
        """diff exits with code 1 for a non-existent file."""
        result = runner.invoke(app, ["diff", "nonexistent.yaml", "also-missing.yaml"])
        assert result.exit_code == 1
        assert "Error loading" in result.output

    def test_diff_invalid_format(self):
        """diff rejects unsupported output formats instead of falling back silently."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--format", "csv"])
            assert result.exit_code == 2
            assert "Unsupported diff format" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_diff_markdown_format(self):
        """diff --format markdown produces migration guide output."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--format", "markdown"])
            assert result.exit_code == 0
            assert "Migration Guide" in result.output or "breaking" in result.output.lower()
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_diff_markdown_output_file(self):
        """diff --format markdown --output writes migration guide to file."""
        old_path, new_path = _identical_specs()
        out_path = tempfile.mktemp(suffix=".md")
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--format", "markdown", "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            assert len(content) > 0
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)

    def test_diff_yaml_format(self):
        """diff --format yaml outputs valid YAML with no changes."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--format", "yaml"])
            assert result.exit_code == 0
            assert "breaking: 0" in result.output
            assert "old_version" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_diff_yaml_output_file(self):
        """diff --format yaml --output writes YAML to a file."""
        old_path, new_path = _identical_specs()
        out_path = tempfile.mktemp(suffix=".yaml")
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--format", "yaml", "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            assert "breaking: 0" in content
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)

    def test_diff_json_output_file(self):
        """diff --format json --output writes JSON to a file."""
        old_path, new_path = _identical_specs()
        out_path = tempfile.mktemp(suffix=".json")
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--format", "json", "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            assert "summary" in content
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)

    def test_diff_invalid_openapi_version(self):
        """diff exits with code 1 when given a Swagger 2.0 (unsupported) spec."""
        old = {
            "swagger": "2.0",
            "info": {"title": "Swagger Petstore", "version": "1.0.0"},
            "paths": {},
        }
        new = {
            "swagger": "2.0",
            "info": {"title": "Swagger Petstore", "version": "1.0.0"},
            "paths": {},
        }
        old_path = _write_yaml(old)
        new_path = _write_yaml(new)
        try:
            result = runner.invoke(app, ["diff", old_path, new_path])
            assert result.exit_code == 1
            assert "Error validating" in result.output or "not supported" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)


class TestCheckCommand:
    """Tests for the ``check`` (CI gating) subcommand."""

    def test_check_with_no_changes(self):
        """check passes when there are no changes."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path])
            assert result.exit_code == 0
            assert "passed" in result.output.lower() or "✓" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_with_breaking_changes(self):
        """check fails (exit 1) when breaking changes are detected."""
        old_path, new_path = _breaking_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path])
            assert result.exit_code == 1
            assert "breaking" in result.output.lower()
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_with_dangerous_changes(self):
        """check passes by default with only dangerous changes."""
        old_path, new_path = _dangerous_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path])
            assert result.exit_code == 0
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_fail_on_dangerous(self):
        """check fails (exit 1) when --fail-on-dangerous is set and dangerous changes exist."""
        old_path, new_path = _dangerous_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path, "--fail-on-dangerous"])
            assert result.exit_code == 1
            assert "dangerous" in result.output.lower()
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_max_dangerous_within_limit(self):
        """check passes when --max-dangerous exceeds the count of dangerous changes."""
        old_path, new_path = _dangerous_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path, "--max-dangerous", "3"])
            assert result.exit_code == 0
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_allow_breaking(self):
        """check passes even with breaking changes when --allow-breaking is used."""
        old_path, new_path = _breaking_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path, "--allow-breaking"])
            assert result.exit_code == 0
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_max_breaking_zero_with_no_changes(self):
        """check passes with --max-breaking=0 when no changes."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path, "--max-breaking", "0"])
            assert result.exit_code == 0
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_output_file(self):
        """check --output writes gate+diff JSON to a file."""
        old_path, new_path = _identical_specs()
        out_path = tempfile.mktemp(suffix=".json")
        try:
            result = runner.invoke(app, ["check", old_path, new_path, "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            assert "gate" in content
            assert "diff" in content
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)

    def test_check_json_format(self):
        """check --format json outputs the structured gate payload."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path, "--format", "json"])
            assert result.exit_code == 0
            assert '"gate"' in result.output
            assert '"diff"' in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_invalid_format(self):
        """check rejects unsupported output formats instead of falling back silently."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path, "--format", "csv"])
            assert result.exit_code != 0
            assert "Unsupported check format" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_yaml_output_file(self):
        """check --format yaml --output writes YAML to a file."""
        old_path, new_path = _identical_specs()
        out_path = tempfile.mktemp(suffix=".yaml")
        try:
            result = runner.invoke(app, ["check", old_path, new_path, "--format", "yaml", "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            payload = yaml.safe_load(content)
            assert isinstance(payload, dict)
            assert "gate" in payload
            assert "diff" in payload
            assert payload["gate"]["passed"] is True
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)

    def test_check_invalid_openapi_version(self):
        """check exits with code 1 when given a Swagger 2.0 (unsupported) spec."""
        old = {
            "swagger": "2.0",
            "info": {"title": "Swagger Petstore", "version": "1.0.0"},
            "paths": {},
        }
        new = {
            "swagger": "2.0",
            "info": {"title": "Swagger Petstore", "version": "1.0.0"},
            "paths": {},
        }
        old_path = _write_yaml(old)
        new_path = _write_yaml(new)
        try:
            result = runner.invoke(app, ["check", old_path, new_path])
            assert result.exit_code == 1
            assert "Error validating" in result.output or "not supported" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)


class TestMigrateCommand:
    """Tests for the ``migrate`` subcommand."""

    def test_migrate_default_format(self):
        """migrate produces a markdown migration guide by default."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["migrate", old_path, new_path])
            assert result.exit_code == 0
            assert result.output.strip()  # non-empty output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_migrate_json_format(self):
        """migrate --format json outputs structured JSON."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["migrate", old_path, new_path, "--format", "json"])
            assert result.exit_code == 0
            assert "summary" in result.output or "changes" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_migrate_output_file(self):
        """migrate --output writes content to a file."""
        old_path, new_path = _identical_specs()
        out_path = tempfile.mktemp(suffix=".md")
        try:
            result = runner.invoke(app, ["migrate", old_path, new_path, "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            assert len(content) > 0
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)

    def test_migrate_yaml_format(self):
        """migrate --format yaml outputs YAML migration guide."""
        old_path, new_path = _nonbreaking_info_specs()
        try:
            result = runner.invoke(app, ["migrate", old_path, new_path, "--format", "yaml"])
            assert result.exit_code == 0
            assert "summary" in result.output or "changes" in result.output
            assert "warning:" in result.output.lower() or "non_breaking" in result.output or "old_version" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_migrate_yaml_output_file(self):
        """migrate --format yaml --output writes YAML to a file."""
        old_path, new_path = _nonbreaking_info_specs()
        out_path = tempfile.mktemp(suffix=".yaml")
        try:
            result = runner.invoke(app, ["migrate", old_path, new_path, "--format", "yaml", "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            assert "non_breaking" in content or "old_version" in content
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)

    def test_migrate_json_output_file(self):
        """migrate --format json --output writes structured JSON to a file."""
        old_path, new_path = _nonbreaking_info_specs()
        out_path = tempfile.mktemp(suffix=".json")
        try:
            result = runner.invoke(app, ["migrate", old_path, new_path, "--format", "json", "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            assert "summary" in content
            assert "non_breaking" in content or "non-breaking" in content
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)

    def test_migrate_invalid_format(self):
        """migrate rejects unsupported output formats instead of falling back silently."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["migrate", old_path, new_path, "--format", "csv"])
            assert result.exit_code == 2
            assert "Unsupported migrate format" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_migrate_invalid_input(self):
        """migrate exits with code 1 for invalid files."""
        result = runner.invoke(app, ["migrate", "no-such-file.yaml", "also-missing.yaml"])
        assert result.exit_code == 1


class TestHelp:
    """Tests for top-level ``--help``."""

    def test_help_contains_commands(self):
        """--help lists all expected subcommands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        for cmd in ["diff", "check", "migrate", "mcp", "version"]:
            assert cmd in result.output

    def test_help_contains_description(self):
        """--help contains the tool description."""
        result = runner.invoke(app, ["--help"])
        assert "breaking changes" in result.output.lower()


class TestMCPCommand:
    """Tests for the ``mcp`` subcommand."""

    def test_mcp_command_exists(self):
        """mcp subcommand is listed in help."""
        result = runner.invoke(app, ["--help"])
        assert "mcp" in result.output


class TestMainModule:
    """Tests for the ``python -m`` entry point (__main__.py)."""

    def test_main_module_version(self):
        """python -m api_contract_guardian version prints version."""
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m", "api_contract_guardian", "version"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        assert result.returncode == 0
        assert "v0.1.0" in result.stdout
